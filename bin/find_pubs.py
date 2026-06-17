#!/usr/bin/env python3
"""
Find publications missing from papers.bib using ORCID.

Usage: python3 bin/find_pubs.py [--add]

Fetches all works from the ORCID profile configured in _data/socials.yml,
compares DOIs against _bibliography/papers.bib, and reports missing entries.

With --add, interactively prompts to add each missing entry.
"""

import json
import os
import re
import sys
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
BIB_FILE = os.path.join(ROOT_DIR, "_bibliography", "papers.bib")
SOCIALS_FILE = os.path.join(ROOT_DIR, "_data", "socials.yml")

MONTHS = {
    "jan": "jan",
    "january": "jan",
    "feb": "feb",
    "february": "feb",
    "mar": "mar",
    "march": "mar",
    "apr": "apr",
    "april": "apr",
    "may": "may",
    "jun": "jun",
    "june": "jun",
    "jul": "jul",
    "july": "jul",
    "aug": "aug",
    "august": "aug",
    "sep": "sep",
    "sept": "sep",
    "september": "sep",
    "oct": "oct",
    "october": "oct",
    "nov": "nov",
    "november": "nov",
    "dec": "dec",
    "december": "dec",
}

ARTICLE_FIELD_ORDER = [
    "title",
    "author",
    "journal",
    "volume",
    "number",
    "pages",
    "year",
    "month",
    "publisher",
    "note",
    "isbn",
    "abbr",
    "doi",
    "url",
]

PROCEEDINGS_FIELD_ORDER = [
    "title",
    "author",
    "booktitle",
    "volume",
    "number",
    "pages",
    "year",
    "month",
    "organization",
    "publisher",
    "location",
    "note",
    "isbn",
    "abbr",
    "doi",
    "url",
]

BOOK_FIELD_ORDER = [
    "title",
    "author",
    "publisher",
    "year",
    "month",
    "isbn",
    "abbr",
    "doi",
    "url",
]

DROP_FIELDS = {"issn"}
TRAILING_FIELDS = {"abbr", "doi", "url"}


def get_orcid_id():
    """Read ORCID ID from _data/socials.yml."""
    with open(SOCIALS_FILE) as f:
        for line in f:
            line = line.strip()
            if line.startswith("orcid_id:"):
                val = line.split(":", 1)[1].strip()
                val = val.split("#")[0].strip()  # remove YAML comment
                return val
    return None


def get_existing_entries():
    """Extract DOIs and titles already in papers.bib."""
    dois = set()
    titles = set()
    keys = set()
    with open(BIB_FILE) as f:
        content = f.read()
    # Extract citation keys
    for m in re.finditer(r'@\w+\s*\{\s*([^,\s]+)', content):
        keys.add(m.group(1).strip().lower())
    # Match doi fields like: doi = {10.xxxx/yyyy}
    for m in re.finditer(r'doi\s*=\s*\{([^}]+)\}', content, re.IGNORECASE):
        dois.add(m.group(1).strip().lower())
    # Match DOIs embedded in URLs
    for m in re.finditer(r'https?://doi\.org/(10\.[^}\s,]+)', content):
        dois.add(m.group(1).strip().lower())
    # Extract titles for fallback matching
    for m in re.finditer(r'title\s*=\s*\{([^}]+)\}', content, re.IGNORECASE):
        # Normalize: lowercase, strip punctuation/whitespace
        t = re.sub(r'[^a-z0-9\s]', '', m.group(1).strip().lower())
        t = re.sub(r'\s+', ' ', t).strip()
        titles.add(t)
    return dois, titles, keys


def normalize_title(title):
    """Normalize a title for comparison."""
    t = re.sub(r'[^a-z0-9\s]', '', title.lower())
    return re.sub(r'\s+', ' ', t).strip()


def fetch_orcid_works(orcid_id):
    """Fetch all works from ORCID public API."""
    url = f"https://pub.orcid.org/v3.0/{orcid_id}/works"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def extract_dois_from_orcid(data):
    """Extract DOIs and titles from ORCID works response."""
    works = []
    for group in data.get("group", []):
        for summary in group.get("work-summary", []):
            title_obj = summary.get("title", {})
            title = ""
            if title_obj and title_obj.get("title"):
                title = title_obj["title"].get("value", "")

            year = ""
            pub_date = summary.get("publication-date")
            if pub_date and pub_date.get("year"):
                year = pub_date["year"].get("value", "")

            doi = None
            for eid in summary.get("external-ids", {}).get("external-id", []):
                if eid.get("external-id-type") == "doi":
                    doi = eid.get("external-id-value")
                    break

            works.append({"title": title, "year": year, "doi": doi})
            break  # only first summary per group
    return works


def fetch_bibtex(doi):
    """Fetch BibTeX from CrossRef via content negotiation."""
    url = f"https://doi.org/{doi}"
    req = urllib.request.Request(url, headers={"Accept": "application/x-bibtex"})
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        return None


def normalize_doi(doi):
    """Strip URL prefixes and normalize a DOI for output."""
    doi = doi.strip()
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    return doi


def read_balanced_value(text, start):
    """Read a BibTeX value starting at start and return (value, next_index)."""
    i = start
    while i < len(text) and text[i].isspace():
        i += 1

    if i >= len(text):
        return "", i

    if text[i] == "{":
        depth = 1
        i += 1
        value_start = i
        while i < len(text) and depth:
            if text[i] == "\\":
                i += 2
                continue
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        return text[value_start : i - 1].strip(), i

    if text[i] == '"':
        i += 1
        value_start = i
        while i < len(text):
            if text[i] == "\\":
                i += 2
                continue
            if text[i] == '"':
                return text[value_start:i].strip(), i + 1
            i += 1
        return text[value_start:i].strip(), i

    value_start = i
    while i < len(text) and text[i] not in ",}":
        i += 1
    return text[value_start:i].strip(), i


def parse_bibtex_entry(bib):
    """Parse a simple BibTeX entry into entry type, key, and fields."""
    text = bib.strip()
    m = re.match(r"@\s*([A-Za-z]+)\s*\{\s*([^,\s]+)\s*,", text)
    if not m:
        return None

    entry_type = m.group(1).lower()
    key = m.group(2).strip()
    fields = {}
    i = m.end()

    while i < len(text):
        while i < len(text) and (text[i].isspace() or text[i] == ","):
            i += 1
        if i >= len(text) or text[i] == "}":
            break

        name_match = re.match(r"([A-Za-z][A-Za-z0-9_-]*)\s*=", text[i:])
        if not name_match:
            i += 1
            continue

        name = name_match.group(1).lower()
        i += name_match.end()
        value, i = read_balanced_value(text, i)
        fields[name] = re.sub(r"\s+", " ", value).strip()

    return entry_type, key, fields


def detect_abbr_from_type(entry_type):
    """Detect entry type and return appropriate abbr."""
    if entry_type in {"inproceedings", "incollection", "proceedings"}:
        return "Proceedings"
    elif entry_type == "book":
        return "Book"
    return "Journal"


def title_word_needs_preserving(word):
    """Return True for acronyms, code names, and BibTeX-sensitive terms."""
    if not word:
        return False
    if re.search(r"[\d+#.]", word):
        return True
    if len(word) == 1 and word.isupper():
        return True
    if len(word) > 1 and word.isupper():
        return True
    return any(c.isupper() for c in word[1:]) and any(c.islower() for c in word)


def capitalize_first_letter(word):
    """Capitalize the first alphabetic character in a word."""
    chars = list(word.lower())
    for i, ch in enumerate(chars):
        if ch.isalpha():
            chars[i] = ch.upper()
            break
    return "".join(chars)


def sentence_case_token(token, capitalize):
    """Sentence-case one token, preserving acronyms and mixed-case code names."""
    if re.search(r"[\d+#.]", token):
        return token

    parts = token.split("-")
    formatted = []
    for i, part in enumerate(parts):
        should_cap = capitalize and i == 0
        if title_word_needs_preserving(part):
            formatted.append(part)
        elif should_cap:
            formatted.append(capitalize_first_letter(part))
        else:
            formatted.append(part.lower())
    return "-".join(formatted)


def read_braced_group(text, start):
    """Read a braced group and return (group_text, next_index)."""
    depth = 0
    i = start
    while i < len(text):
        if text[i] == "\\":
            i += 2
            continue
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1], i + 1
        i += 1
    return text[start:], len(text)


def sentence_case_title(title):
    """Use sentence case for titles, capitalizing the start and after colons."""
    result = []
    capitalize = True
    i = 0

    while i < len(title):
        ch = title[i]

        if ch == "{":
            group, i = read_braced_group(title, i)
            result.append(group)
            if re.search(r"[A-Za-z]", group):
                capitalize = False
            continue

        word_match = re.match(r"[A-Za-z0-9+#.]+(?:-[A-Za-z0-9+#.]+)*", title[i:])
        if word_match:
            token = word_match.group(0)
            result.append(sentence_case_token(token, capitalize))
            capitalize = False
            i += len(token)
            continue

        result.append(ch)
        if ch == ":":
            capitalize = True
        elif not ch.isspace() and ch not in "\"'([{":
            # Punctuation other than colon does not start a new title phrase.
            capitalize = False
        i += 1

    return "".join(result)


def normalize_month(value):
    """Convert month names from CrossRef into BibTeX month macros."""
    return MONTHS.get(value.strip().strip("{}").lower())


def normalize_pages(value):
    """Use BibTeX page-range separators for numeric ranges."""
    return re.sub(r"(?<=\d)\s*[-–—]\s*(?=\d)", "--", value)


def format_field(name, value):
    """Format one BibTeX field using local spacing conventions."""
    if name == "month":
        month = normalize_month(value)
        if month:
            return f"  {name} = {month},"
    return f"  {name} = {{{value}}},"


def citation_key_from_fields(fields, fallback_key, used_keys):
    """Build a local-style citation key such as liu2026fishtank."""
    author = fields.get("author", "")
    first_author = re.split(r"\s+and\s+", author, maxsplit=1, flags=re.IGNORECASE)[0].strip()
    if "," in first_author:
        surname = first_author.split(",", 1)[0]
    else:
        surname = first_author.split()[-1] if first_author.split() else ""

    year = fields.get("year", "")
    title = re.sub(r"\{[^}]*\}", " ", fields.get("title", ""))
    title_words = re.findall(r"[A-Za-z0-9]+", title)
    title_word = next((w for w in title_words if w.lower() not in {"a", "an", "the"}), "")

    base = "".join([surname, year, title_word])
    base = re.sub(r"[^A-Za-z0-9]", "", base).lower()
    if not base:
        base = re.sub(r"[^A-Za-z0-9]", "", fallback_key).lower() or "publication"

    key = base
    suffix = 2
    while key.lower() in used_keys:
        key = f"{base}{suffix}"
        suffix += 1
    return key


def field_order_for_type(entry_type):
    """Return the preferred field order for a BibTeX entry type."""
    if entry_type in {"inproceedings", "incollection", "proceedings"}:
        return PROCEEDINGS_FIELD_ORDER
    if entry_type == "book":
        return BOOK_FIELD_ORDER
    return ARTICLE_FIELD_ORDER


def ordered_field_names(entry_type, fields):
    """Return field names in local display order."""
    field_order = field_order_for_type(entry_type)
    known = [name for name in field_order if name in fields]
    remaining = sorted(
        name
        for name in fields
        if name not in field_order and name not in DROP_FIELDS and name not in TRAILING_FIELDS
    )
    trailing = [name for name in field_order if name in TRAILING_FIELDS and name in fields]
    return [name for name in known if name not in TRAILING_FIELDS] + remaining + trailing


def format_bibtex_entry(bib, doi, used_keys):
    """Parse and format CrossRef BibTeX using local bibliography conventions."""
    parsed = parse_bibtex_entry(bib)
    if not parsed:
        return None, None

    entry_type, fallback_key, fields = parsed
    doi = normalize_doi(doi)

    fields = {name: value for name, value in fields.items() if name not in DROP_FIELDS}
    if "title" in fields:
        fields["title"] = sentence_case_title(fields["title"])
    if "pages" in fields:
        fields["pages"] = normalize_pages(fields["pages"])
    fields["doi"] = doi
    fields["abbr"] = detect_abbr_from_type(entry_type)
    fields["url"] = f"https://doi.org/{doi}"

    key = citation_key_from_fields(fields, fallback_key, used_keys)
    lines = [f"@{entry_type}{{{key},"]
    for name in ordered_field_names(entry_type, fields):
        lines.append(format_field(name, fields[name]))
    lines.append("}")
    return "\n".join(lines), key


def main():
    add_mode = "--add" in sys.argv

    orcid_id = get_orcid_id()
    if not orcid_id:
        print("Error: No orcid_id found in _data/socials.yml")
        sys.exit(1)

    print(f"ORCID: {orcid_id}")
    print(f"Fetching publications from ORCID...")

    existing_dois, existing_titles, existing_keys = get_existing_entries()
    orcid_data = fetch_orcid_works(orcid_id)
    works = extract_dois_from_orcid(orcid_data)

    print(f"Found {len(works)} works on ORCID, {len(existing_dois)} DOIs + {len(existing_titles)} titles in papers.bib\n")

    missing = []
    for w in works:
        # Check by DOI
        if w["doi"] and w["doi"].lower() in existing_dois:
            continue
        # Check by title
        if normalize_title(w["title"]) in existing_titles:
            continue
        # Not found
        if not w["doi"]:
            print(f"  [no DOI] {w['title']} ({w['year']})")
        else:
            missing.append(w)

    if not missing:
        print("All ORCID publications are already in papers.bib!")
        return

    print(f"--- {len(missing)} missing publication(s) ---\n")

    for i, w in enumerate(missing, 1):
        print(f"[{i}/{len(missing)}] {w['title']} ({w['year']})")
        print(f"  DOI: {w['doi']}")

        if add_mode:
            bib = fetch_bibtex(w["doi"])
            if not bib:
                print("  Could not fetch BibTeX. Skipping.\n")
                continue

            bib, key = format_bibtex_entry(bib, w["doi"], existing_keys)
            if not bib:
                print("  Could not parse BibTeX. Skipping.\n")
                continue

            print()
            print(bib)
            print()

            answer = input("  Add to papers.bib? [y/N/q] ").strip().lower()
            if answer == "q":
                print("Quit.")
                return
            elif answer == "y":
                with open(BIB_FILE, "a") as f:
                    f.write("\n" + bib + "\n")
                existing_keys.add(key.lower())
                print("  -> Added!\n")
            else:
                print("  -> Skipped.\n")
        else:
            print()

    if not add_mode and missing:
        print("Run with --add to interactively add missing publications:")
        print(f"  python3 bin/find_pubs.py --add")


if __name__ == "__main__":
    main()
