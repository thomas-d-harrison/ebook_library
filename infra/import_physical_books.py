"""
Add physical bookshelf inventory (CSV) to the ebook library SQLite database.

What it does
  * creates a `formats` lookup table (epub, mobi, azw3, pdf, physical, ...) with a
    medium of 'digital' or 'physical'
  * adds `format_id` to `book_files` and backfills it from the existing file types.
    A physical copy is a `book_files` row with format 'physical' and no file path.
  * matches each CSV row to an existing `books` row (title + author); matched books
    simply gain a physical copy
  * unmatched rows become NEW `books` rows (no folder), with authors created/reused
  * rows titled "Unidentified ..." are skipped entirely
  * looks up genres (subjects) and other missing metadata for physical-only books on
    Google Books, falling back to Open Library, and fills them in (needs internet;
    skip with --no-lookup). Existing values are never overwritten.
  * creates a `v_book_ownership` view (ebook only / physical only / both)
  * safe to re-run (only missing copies are added); DB is backed up first

Usage (script, .db and .csv in the same folder):
    python import_physical_books.py --dry-run     # preview only, writes nothing
    python import_physical_books.py               # do it
Optional: --db other.db --csv other.csv --no-lookup
"""
import argparse, csv, difflib, json, re, shutil, sqlite3, sys, tempfile, time, unicodedata
import urllib.error, urllib.parse, urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent

SCHEMA = """
CREATE TABLE IF NOT EXISTS formats (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name   TEXT UNIQUE NOT NULL,
    medium TEXT NOT NULL CHECK(medium IN ('digital','physical'))
);
INSERT OR IGNORE INTO formats (name, medium) VALUES
    ('epub','digital'),('mobi','digital'),('azw3','digital'),('pdf','digital'),
    ('physical','physical'),('hardcover','physical'),('paperback','physical');
"""

VIEW = """
DROP VIEW IF EXISTS v_book_ownership;
CREATE VIEW v_book_ownership AS
SELECT b.id AS book_id,
       b.title,
       (SELECT group_concat(a.author_name, ', ')
          FROM book_authors ba JOIN authors a ON a.id = ba.author_id
         WHERE ba.book_id = b.id) AS authors,
       (SELECT COUNT(*) FROM book_files f JOIN formats x ON x.id = f.format_id
         WHERE f.book_id = b.id AND x.medium = 'digital')  AS digital_copies,
       (SELECT COUNT(*) FROM book_files f JOIN formats x ON x.id = f.format_id
         WHERE f.book_id = b.id AND x.medium = 'physical') AS physical_copies,
       CASE
         WHEN EXISTS (SELECT 1 FROM book_files f JOIN formats x ON x.id = f.format_id
                       WHERE f.book_id = b.id AND x.medium = 'digital')
          AND EXISTS (SELECT 1 FROM book_files f JOIN formats x ON x.id = f.format_id
                       WHERE f.book_id = b.id AND x.medium = 'physical') THEN 'both'
         WHEN EXISTS (SELECT 1 FROM book_files f JOIN formats x ON x.id = f.format_id
                       WHERE f.book_id = b.id AND x.medium = 'physical') THEN 'physical only'
         ELSE 'ebook only'
       END AS ownership
FROM books b;
"""

# ---------------------------------------------------------------- helpers
def fold(s):
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(ch for ch in s if not unicodedata.combining(ch))

def norm_title(t):
    t = fold(t).lower()
    t = re.sub(r"\([^)]*\)", "", t)            # drop "(Dark Tower I)", "(Author's ... Edition)"
    t = t.split(":")[0]                         # drop subtitle
    t = t.replace("&", " and ").replace("'", "").replace("’", "")
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    t = re.sub(r"^(the|a|an) ", "", " ".join(t.split()))
    return t

def author_key(name):                           # "George R.R. Martin" == "George R. R. Martin"
    return re.sub(r"[^a-z]", "", fold(name).lower())

def last_name(name):
    n = re.sub(r",?\s+(jr|sr)\.?$", "", fold(name).lower().strip())
    w = re.findall(r"[a-z']+", n)
    return w[-1] if w else ""

def split_authors(raw):
    """'John & Geri McPherson' -> ['John McPherson','Geri McPherson'];  'X (ed.)' -> ['X']"""
    raw = (raw or "").replace("?", "")
    raw = re.sub(r"\(ed\.\)", "", raw).strip()
    parts = [p.strip() for p in re.split(r";|\s&\s|\sand\s", raw) if p.strip()]
    if len(parts) > 1 and len(parts[0].split()) == 1 and len(parts[-1].split()) > 1:
        parts[0] += " " + parts[-1].split()[-1]
    return parts

def split_name(name):
    w = name.split()
    first = " ".join(w[:-1]) if len(w) > 1 else None
    last = w[-1] if w else name
    if re.fullmatch(r"(jr|sr)\.?", last, re.I) and len(w) > 2:
        last, first = " ".join(w[-2:]), " ".join(w[:-2])
    return first, last

def authors_compatible(csv_author, db_authors):
    cl = [last_name(a) for a in split_authors(csv_author)]
    if not cl:
        return True                              # CSV has no author -> title alone decides
    dl = [last_name(a) for a in db_authors]
    return any(c == d or difflib.SequenceMatcher(None, c, d).ratio() >= 0.85
               for c in cl for d in dl)

# ---------------------------------------------------------------- metadata lookup
LANG = {"en": "eng", "es": "spa", "fr": "fra", "de": "deu", "it": "ita", "ru": "rus",
        "pt": "por", "ja": "jpn", "zh": "zho", "la": "lat", "nl": "nld", "ar": "ara"}
NOISE = re.compile(r"accessible book|protected daisy|in library|large type|lending library|"
                   r"internet archive|new york times|overdrive|staff picks|reading level|"
                   r"^nyt:|^open library|bestseller|^\d{4}$|translations? into|"
                   r"^fiction, general$|^general$", re.I)

def http_get_json(url, retries=3):
    """GET a JSON document. Returns None on a normal failure; raises ConnectionError if
    the network itself is unreachable (so we can stop instead of hammering)."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ebook-library-importer/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                time.sleep(2 * (attempt + 1))
                continue
            return None
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt == retries - 1:
                raise ConnectionError(str(e))
            time.sleep(1)
        except ValueError:
            return None
    return None

def _title_ok(found, wanted):
    a, b = norm_title(found), norm_title(wanted)
    return bool(a and b) and (a == b or difflib.SequenceMatcher(None, a, b).ratio() >= 0.85)

def _authors_ok(found_list, wanted):
    if not wanted:
        return True
    want = [last_name(x) for x in wanted]
    have = [last_name(x) for x in (found_list or [])]
    return any(w == h or difflib.SequenceMatcher(None, w, h).ratio() >= 0.85 for w in want for h in have)

def clean_subjects(raw):
    out, seen = [], set()
    for part in raw:
        for piece in re.split(r"\s*/\s*", part or ""):
            piece = piece.strip()
            if not piece or len(piece) > 40 or NOISE.search(piece):
                continue
            if piece.islower():
                piece = piece[0].upper() + piece[1:]
            if piece.lower() not in seen:
                seen.add(piece.lower())
                out.append(piece)
    return out[:8]

def lookup_google(title, author):
    q = f'intitle:"{title}"' + (f' inauthor:"{author}"' if author else "")
    data = http_get_json("https://www.googleapis.com/books/v1/volumes?" + urllib.parse.urlencode(
        {"q": q, "maxResults": 5, "printType": "books"}))
    meta = {}
    for item in (data or {}).get("items", []):
        vi = item.get("volumeInfo", {})
        if not _title_ok(vi.get("title", ""), title) or not _authors_ok(vi.get("authors"), [author] if author else []):
            continue
        meta.setdefault("subjects", clean_subjects(vi.get("categories", [])))
        if not meta["subjects"]:
            del meta["subjects"]
        for key, val in (("description", vi.get("description")), ("publisher", vi.get("publisher")),
                         ("publish_date", vi.get("publishedDate")),
                         ("language", LANG.get(vi.get("language", ""), vi.get("language"))),
                         ("google_id", item.get("id"))):
            if val and key not in meta:
                meta[key] = val
        for ident in vi.get("industryIdentifiers", []):
            if ident.get("type") == "ISBN_13" and "isbn" not in meta:
                meta["isbn"] = ident["identifier"]
    return meta

def lookup_openlibrary(title, author):
    params = {"title": title, "limit": 5, "fields": "title,author_name,subject,first_publish_year,publisher,isbn"}
    if author:
        params["author"] = author
    data = http_get_json("https://openlibrary.org/search.json?" + urllib.parse.urlencode(params))
    for d in (data or {}).get("docs", []):
        if not _title_ok(d.get("title", ""), title) or not _authors_ok(d.get("author_name"), [author] if author else []):
            continue
        meta = {}
        subs = clean_subjects(d.get("subject", []))
        if subs:
            meta["subjects"] = subs
        if d.get("first_publish_year"):
            meta["publish_date"] = str(d["first_publish_year"])
        if d.get("publisher"):
            meta["publisher"] = d["publisher"][0]
        isbn13 = next((i for i in d.get("isbn", []) if len(i) == 13), None)
        if isbn13:
            meta["isbn"] = isbn13
        if meta:
            return meta
    return {}

def lookup_metadata(title, author):
    """Genres + basics for one book. Google Books first; Open Library fills any gap."""
    clean_title = re.sub(r"\s*\(.*?\)\s*", " ", title).split(":")[0].strip()
    meta = lookup_google(clean_title, author)
    if not meta.get("subjects"):
        for k, v in lookup_openlibrary(clean_title, author).items():
            meta.setdefault(k, v)
    return meta

def apply_metadata(con, book_id, meta):
    con.execute("""UPDATE books SET
                     description  = CASE WHEN description  IS NULL OR description  = '' THEN ? ELSE description  END,
                     publisher    = CASE WHEN publisher    IS NULL OR publisher    = '' THEN ? ELSE publisher    END,
                     publish_date = CASE WHEN publish_date IS NULL OR publish_date = '' THEN ? ELSE publish_date END,
                     language     = CASE WHEN language     IS NULL OR language     = '' THEN ? ELSE language     END
                   WHERE id = ?""",
                (meta.get("description"), meta.get("publisher"), meta.get("publish_date"),
                 meta.get("language"), book_id))
    for name in meta.get("subjects", []):
        row = con.execute("SELECT id FROM subjects WHERE lower(subject_name) = lower(?)", (name,)).fetchone()
        sid = row[0] if row else con.execute("INSERT INTO subjects (subject_name) VALUES (?)", (name,)).lastrowid
        con.execute("INSERT OR IGNORE INTO book_subjects (book_id, subject_id) VALUES (?, ?)", (book_id, sid))
    for typ, val in (("ISBN", meta.get("isbn")), ("GOOGLE", meta.get("google_id"))):
        if val:
            con.execute("INSERT OR IGNORE INTO book_identifiers (book_id, identifier_type, identifier_value) "
                        "VALUES (?, ?, ?)", (book_id, typ, val))

def fill_missing_metadata(con, cache_path, dry_run):
    """Look up genres for every physical-only book that has none (new books, earlier misses)."""
    targets = con.execute("""
        SELECT b.id, b.title, (SELECT a.author_name FROM book_authors ba JOIN authors a ON a.id = ba.author_id
                                WHERE ba.book_id = b.id ORDER BY a.id LIMIT 1)
          FROM v_book_ownership v JOIN books b ON b.id = v.book_id
         WHERE v.ownership = 'physical only'
           AND NOT EXISTS (SELECT 1 FROM book_subjects bs WHERE bs.book_id = b.id)""").fetchall()
    if not targets:
        return 0, []
    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    except (OSError, ValueError):
        cache = {}
    print(f"\nLooking up genres for {len(targets)} physical-only books ...")
    found, missed = 0, []
    for n, (bid, title, author) in enumerate(targets, 1):
        key = f"{norm_title(title)}|{last_name(author or '')}"
        meta = cache.get(key)
        if meta is None:
            try:
                meta = lookup_metadata(title, author)
            except ConnectionError as e:
                print(f"  Network unavailable ({e}); skipping lookups. Re-run later to fill genres.")
                return found, missed + [t for _, t, _ in targets[n - 1:]]
            if meta:                             # only remember hits, so misses are retried next run
                cache[key] = meta
            time.sleep(0.4)                      # be polite to the free APIs
        if meta.get("subjects"):
            apply_metadata(con, bid, meta)
            found += 1
        else:
            if meta:
                apply_metadata(con, bid, meta)   # basics even when no genre was found
            missed.append(title)
        if n % 25 == 0:
            print(f"  {n}/{len(targets)} ...")
    if not dry_run:
        try:
            cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=0), encoding="utf-8")
        except OSError:
            pass
    return found, missed

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(HERE / "data/tt_db_ebook_lib.db"))
    ap.add_argument("--csv", default=str(HERE / "data/tt_bookshelf_inventory.csv"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-lookup", action="store_true", help="skip the online genre lookup")
    args = ap.parse_args()
    db_path, csv_path = Path(args.db), Path(args.csv)
    for p in (db_path, csv_path):
        if not p.exists():
            sys.exit(f"Not found: {p}")

    if not args.dry_run:
        bak = db_path.with_name(f"{db_path.stem}.backup-{datetime.now():%Y%m%d-%H%M%S}{db_path.suffix}")
        shutil.copy2(db_path, bak)
        print(f"Backup written: {bak.name}")

    work_path, tmpdir = db_path, None
    if args.dry_run:                             # dry run works on a throw-away copy
        tmpdir = tempfile.mkdtemp()
        work_path = Path(tmpdir) / db_path.name
        shutil.copy2(db_path, work_path)
    con = sqlite3.connect(work_path)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA)

    # --- add + backfill book_files.format_id
    cols = [r[1] for r in con.execute("PRAGMA table_info(book_files)")]
    if "format_id" not in cols:
        con.execute("ALTER TABLE book_files ADD COLUMN format_id INTEGER REFERENCES formats(id)")
    for (ext,) in con.execute("SELECT DISTINCT lower(trim(file_format,'. ')) FROM book_files "
                              "WHERE format_id IS NULL AND file_format IS NOT NULL").fetchall():
        con.execute("INSERT OR IGNORE INTO formats (name, medium) VALUES (?, 'digital')", (ext,))
    con.execute("UPDATE book_files SET format_id = (SELECT id FROM formats "
                "WHERE name = lower(trim(book_files.file_format,'. '))) "
                "WHERE format_id IS NULL AND file_format IS NOT NULL")
    physical_id = con.execute("SELECT id FROM formats WHERE name='physical'").fetchone()[0]

    # --- indexes of what's already in the library
    book_authors = {}
    for bid, name in con.execute("SELECT ba.book_id, a.author_name FROM book_authors ba "
                                 "JOIN authors a ON a.id = ba.author_id"):
        book_authors.setdefault(bid, []).append(name)
    title_idx = {}
    for bid, title in con.execute("SELECT id, title FROM books"):
        title_idx.setdefault(norm_title(title), []).append((bid, title))
    author_idx = {author_key(n): i for i, n in con.execute("SELECT id, author_name FROM authors")}

    def find_book(title, author):
        nt = norm_title(title)
        hits = [b for b in title_idx.get(nt, []) if authors_compatible(author, book_authors.get(b[0], []))]
        if hits:
            return hits[0][0], "exact", len(hits) > 1
        best, best_r = None, 0
        for k, lst in title_idx.items():
            r = difflib.SequenceMatcher(None, nt, k).ratio()
            if r >= 0.80 and r > best_r:
                cand = [b for b in lst if author and authors_compatible(author, book_authors.get(b[0], []))]
                if cand:
                    best, best_r = cand[0][0], r
        return (best, "fuzzy", False) if best else (None, None, False)

    def get_author_id(name):
        k = author_key(name)
        if k in author_idx:
            return author_idx[k], False
        for k2, aid in author_idx.items():       # near-duplicate spelling
            if difflib.SequenceMatcher(None, k, k2).ratio() >= 0.92:
                return aid, False
        first, last = split_name(name)
        cur = con.execute("INSERT INTO authors (author_name, author_sort, first_name, last_name, sex) "
                          "VALUES (?,?,?,?,NULL)",
                          (name, f"{last}, {first}" if first else last, first, last))
        author_idx[k] = cur.lastrowid
        return cur.lastrowid, True

    # --- process CSV: work out how many physical copies each book should have
    wanted, report = {}, []
    stats = dict(exact=0, fuzzy=0, new=0, unidentified=0, new_authors=0)
    with open(csv_path, encoding="utf-8-sig", newline="") as fh:
        for n, row in enumerate(csv.DictReader(fh), start=2):
            title = (row.get("Title") or "").strip()
            author = (row.get("Author") or "").strip()
            if not title:
                continue
            if title.lower().startswith("unidentified"):
                stats["unidentified"] += 1
                report.append((n, title, author, "skipped", None, 0))
                continue
            book_id, method, ambiguous = find_book(title, author)
            review = 1 if method == "fuzzy" or ambiguous else 0
            if book_id is None:
                method = "new"
                clean = re.sub(r"\s*\((?!.*Edition).*?\)\s*$", "", title)   # "(The Dark Tower I)" dropped
                cur = con.execute("INSERT INTO books (title) VALUES (?)", (clean,))
                book_id = cur.lastrowid
                title_idx.setdefault(norm_title(title), []).append((book_id, title))
                names = split_authors(author)
                book_authors[book_id] = names
                for nm in names:
                    aid, created = get_author_id(nm)
                    stats["new_authors"] += created
                    con.execute("INSERT OR IGNORE INTO book_authors (book_id, author_id) VALUES (?,?)",
                                (book_id, aid))
            stats[method] += 1
            wanted[book_id] = wanted.get(book_id, 0) + 1
            report.append((n, title, author, method, book_id, review))

    added = 0
    for book_id, want in wanted.items():
        have = con.execute("SELECT COUNT(*) FROM book_files f JOIN formats x ON x.id=f.format_id "
                           "WHERE f.book_id=? AND x.medium='physical'", (book_id,)).fetchone()[0]
        for _ in range(max(0, want - have)):
            con.execute("INSERT INTO book_files (book_id, file_path, file_format, file_size, format_id) "
                        "VALUES (?, NULL, NULL, NULL, ?)", (book_id, physical_id))
            added += 1
    con.executescript(VIEW)

    genres_found, genres_missed = (0, [])
    if not args.no_lookup:
        genres_found, genres_missed = fill_missing_metadata(
            con, db_path.with_name("metadata_lookup_cache.json"), args.dry_run)

    # --- report
    rpt = csv_path.with_name("physical_import_report.csv")
    if not args.dry_run:
        with open(rpt, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["csv_line", "title", "author", "match", "book_id", "needs_review"])
            w.writerows(report)
    print(f"\n{'DRY RUN - nothing saved' if args.dry_run else 'Import complete'}")
    print(f"  matched existing books  : {stats['exact']} exact + {stats['fuzzy']} fuzzy (check these)")
    print(f"  new physical-only books : {stats['new']}  (new authors created: {stats['new_authors']})")
    print(f"  unidentified, skipped   : {stats['unidentified']}")
    print(f"  physical copies added   : {added}")
    for r in report:
        if r[5]:
            print(f"  REVIEW line {r[0]}: {r[1]!r} [{r[3]}] -> book_id {r[4]}")
    if not args.no_lookup:
        print(f"  genres found online     : {genres_found}  (not found: {len(genres_missed)})")
        for t in genres_missed:
            print(f"    no genre match: {t}")
    if not args.dry_run:
        print(f"  report: {rpt.name}")

    if args.dry_run:
        con.close()
        shutil.rmtree(tmpdir, ignore_errors=True)
        return
    else:
        con.commit()
        print("\nOwnership summary:")
        for o, c in con.execute("SELECT ownership, COUNT(*) FROM v_book_ownership GROUP BY 1"):
            print(f"  {o:14s} {c}")
    con.close()

if __name__ == "__main__":
    main()