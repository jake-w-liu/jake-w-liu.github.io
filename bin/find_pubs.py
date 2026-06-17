#!/usr/bin/env python3
"""
Find publications missing from papers.bib using ORCID.

Usage: python3 bin/find_pubs.py [--add] [--sync-cv]

Fetches all works from the ORCID profile configured in _data/socials.yml,
compares DOIs against _bibliography/papers.bib, and reports missing entries.

With --add, interactively prompts to add each missing entry and then syncs
cv/Jake_W_Liu_CV.tex from _bibliography/papers.bib.

With --sync-cv, syncs the CV publication list without contacting ORCID.
"""

from datetime import date
import json
import os
import re
import sys
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
BIB_FILE = os.path.join(ROOT_DIR, "_bibliography", "papers.bib")
CV_FILE = os.path.join(ROOT_DIR, "cv", "Jake_W_Liu_CV.tex")
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

MONTH_NUMBERS = {
    "jan": 1,
    "january": 1,
    "1": 1,
    "01": 1,
    "feb": 2,
    "february": 2,
    "2": 2,
    "02": 2,
    "mar": 3,
    "march": 3,
    "3": 3,
    "03": 3,
    "apr": 4,
    "april": 4,
    "4": 4,
    "04": 4,
    "may": 5,
    "5": 5,
    "05": 5,
    "jun": 6,
    "june": 6,
    "6": 6,
    "06": 6,
    "jul": 7,
    "july": 7,
    "7": 7,
    "07": 7,
    "aug": 8,
    "august": 8,
    "8": 8,
    "08": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "9": 9,
    "09": 9,
    "oct": 10,
    "october": 10,
    "10": 10,
    "nov": 11,
    "november": 11,
    "11": 11,
    "dec": 12,
    "december": 12,
    "12": 12,
}

MONTH_LABELS = {
    1: "Jan.",
    2: "Feb.",
    3: "Mar.",
    4: "Apr.",
    5: "May",
    6: "Jun.",
    7: "Jul.",
    8: "Aug.",
    9: "Sep.",
    10: "Oct.",
    11: "Nov.",
    12: "Dec.",
}

FULL_MONTH_LABELS = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}

CV_GROUPS = [
    ("book", "Book", "B"),
    ("journal", "Journal Articles", "J"),
    ("conference", "Conference Papers", "C"),
]

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
CANONICAL_TITLE_TERMS = {
    term.lower(): term
    for term in (
        "ACES",
        "API",
        "CPU",
        "DFT",
        "DOI",
        "EVM",
        "FDTD",
        "FFT",
        "GPU",
        "GTD",
        "ICCEM",
        "IEEE",
        "Julia",
        "Kouyoumjian",
        "MATLAB",
        "Pathak",
        "PEC",
        "PSTD",
        "RF",
        "RFIT",
        "SPIE",
        "URSI",
        "UTD",
        "UTDKernels.jl",
    )
}


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


def iter_bibtex_entries(content):
    """Yield complete BibTeX entries from a bibliography file."""
    i = 0
    while i < len(content):
        at = content.find("@", i)
        if at == -1:
            break

        brace = content.find("{", at)
        if brace == -1:
            break

        depth = 0
        j = brace
        while j < len(content):
            if content[j] == "\\":
                j += 2
                continue
            if content[j] == "{":
                depth += 1
            elif content[j] == "}":
                depth -= 1
                if depth == 0:
                    yield content[at : j + 1]
                    i = j + 1
                    break
            j += 1
        else:
            break


def get_existing_entries():
    """Extract DOIs and titles already in papers.bib."""
    dois = set()
    titles = set()
    keys = set()
    with open(BIB_FILE) as f:
        content = f.read()

    for entry in iter_bibtex_entries(content):
        parsed = parse_bibtex_entry(entry)
        if not parsed:
            continue

        _, key, fields = parsed
        keys.add(key.lower())

        if fields.get("doi"):
            dois.add(normalize_doi(fields["doi"]).lower())
        if fields.get("url"):
            m = re.search(r"https?://(?:dx\.)?doi\.org/(10\.[^}\s,]+)", fields["url"], re.IGNORECASE)
            if m:
                dois.add(normalize_doi(m.group(1)).lower())
        if fields.get("title"):
            titles.add(normalize_title(fields["title"]))

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
    """Return True for code names and BibTeX-sensitive terms."""
    if not word:
        return False
    if re.search(r"[\d+#.]", word):
        return True
    if len(word) == 1 and word.isupper():
        return True
    return any(c.isupper() for c in word[1:]) and any(c.islower() for c in word)


def canonical_title_term(token):
    """Return local preferred casing for known title terms."""
    return CANONICAL_TITLE_TERMS.get(token.lower())


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
    canonical = canonical_title_term(token)
    if canonical:
        return canonical
    if re.search(r"[\d+#.]", token):
        return token

    parts = token.split("-")
    formatted = []
    for i, part in enumerate(parts):
        should_cap = capitalize and i == 0
        canonical = canonical_title_term(part)
        if canonical:
            formatted.append(canonical)
        elif title_word_needs_preserving(part):
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


def entry_group(entry_type):
    """Return the CV publication group for a BibTeX entry type."""
    if entry_type == "book":
        return "book"
    if entry_type in {"inproceedings", "incollection", "proceedings"}:
        return "conference"
    return "journal"


def month_number(value):
    """Return a numeric month for BibTeX month strings and macros."""
    if not value:
        return 0
    return MONTH_NUMBERS.get(value.strip().strip("{}").lower(), 0)


def year_number(value):
    """Return a numeric year, or zero when unavailable."""
    if not value:
        return 0
    m = re.search(r"\d{4}", value)
    return int(m.group(0)) if m else 0


def publication_sort_key(publication):
    """Sort newest publications first, preserving bibliography order on ties."""
    fields = publication["fields"]
    return (-year_number(fields.get("year")), -month_number(fields.get("month")), publication["index"])


def latex_escape_text(value):
    """Escape text for LaTeX while preserving existing LaTeX commands."""
    if not value:
        return ""

    specials = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }

    out = []
    i = 0
    while i < len(value):
        ch = value[i]
        if ch == "–":
            out.append("--")
            i += 1
            continue
        if ch == "—":
            out.append("---")
            i += 1
            continue
        if ch == "\\":
            out.append(ch)
            i += 1
            if i < len(value):
                out.append(value[i])
                i += 1
            continue
        out.append(specials.get(ch, ch))
        i += 1
    return "".join(out)


def latex_escape_url(value):
    """Escape URL characters that are special in LaTeX macro arguments."""
    return latex_escape_text(value)


def latex_to_plain(value):
    """Convert the subset of LaTeX used in the CV to plain text for matching."""
    text = value or ""
    text = text.replace(r"\name", "Jake W. Liu")
    text = re.sub(r"\\([#$%&_{}])", r"\1", text)
    text = re.sub(r"\\textasciitilde\{\}", "~", text)
    text = re.sub(r"\\textasciicircum\{\}", "^", text)
    text = re.sub(r"\\[A-Za-z]+\*?", " ", text)
    text = text.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", text).strip()


def bibtex_to_plain(value):
    """Convert BibTeX field text to plain text for matching."""
    text = value or ""
    text = re.sub(r"\\([#$%&_{}])", r"\1", text)
    text = re.sub(r"\\[A-Za-z]+\*?", " ", text)
    text = text.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", text).strip()


def normalize_doi_for_match(doi):
    """Normalize a DOI for identity matching."""
    return normalize_doi(latex_to_plain(doi)).lower()


def doi_from_fields(fields):
    """Extract a DOI from BibTeX DOI or DOI URL fields."""
    if fields.get("doi"):
        return normalize_doi(fields["doi"]).lower()
    if fields.get("url"):
        m = re.search(r"https?://(?:dx\.)?doi\.org/(10\.[^}\s,]+)", fields["url"], re.IGNORECASE)
        if m:
            return normalize_doi(m.group(1)).lower()
    return ""


def read_latex_command_argument(text, command, arg_index=0, start=0):
    """Read a braced argument from a LaTeX command call."""
    pos = text.find(command, start)
    if pos == -1:
        return None, -1

    i = pos + len(command)
    for _ in range(arg_index + 1):
        while i < len(text) and text[i].isspace():
            i += 1
        if i >= len(text) or text[i] != "{":
            return None, -1
        group, i = read_braced_group(text, i)
    return group[1:-1], i


def first_href_label(text):
    """Return the first visible label used in a CV href."""
    label, _ = read_latex_command_argument(text, r"\href", arg_index=1)
    return label


def cv_item_dois(item):
    """Return all DOI identities visible in a CV item."""
    dois = set()
    for doi in re.findall(r"\\pubdoi\{([^{}]+)\}", item):
        dois.add(normalize_doi_for_match(doi))
    for doi in re.findall(r"https?://(?:dx\.)?doi\.org/(10\.[^}\s]+)", item, flags=re.IGNORECASE):
        dois.add(normalize_doi_for_match(doi))
    return {doi for doi in dois if doi}


def cv_item_title(item):
    """Return a normalized title identity for a CV item."""
    href_label = first_href_label(item)
    if href_label:
        return normalize_title(latex_to_plain(href_label))

    m = re.search(r"``(.+?)\.''", item, flags=re.DOTALL)
    if m:
        return normalize_title(latex_to_plain(m.group(1)))
    return ""


def split_cv_items(body):
    """Split an enumerate body into CV item blocks."""
    matches = list(re.finditer(r"(?m)^[ \t]*\\item\b", body))
    items = []
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        item = body[match.start() : end].strip()
        if item.startswith(r"\item"):
            item = "  " + item
        if item:
            items.append(item)
    return items


def parse_existing_cv_publications(cv_content):
    """Read existing CV publication items so hand-edited entries are preserved."""
    groups = {group: [] for group, _, _ in CV_GROUPS}
    section_match = re.search(r"\\section\*\{Publications\}", cv_content)
    if not section_match:
        return groups

    end_match = re.search(r"\n\\end\{document\}", cv_content[section_match.start() :])
    section_end = section_match.start() + end_match.start() if end_match else len(cv_content)
    section = cv_content[section_match.start() : section_end]

    subsection_pattern = re.compile(
        r"\\subsection\*\{(?P<title>[^{}]+)\}\s*"
        r"\\begin\{enumerate\}\[label=\{\[(?P<label>[A-Z])\\arabic\*\]\}\]\s*"
        r"(?P<body>.*?)"
        r"\\end\{enumerate\}",
        flags=re.DOTALL,
    )
    title_to_group = {title: group for group, title, _ in CV_GROUPS}

    for match in subsection_pattern.finditer(section):
        group = title_to_group.get(match.group("title"))
        if not group:
            continue
        for item in split_cv_items(match.group("body")):
            groups[group].append(
                {
                    "item": item,
                    "dois": cv_item_dois(item),
                    "title": cv_item_title(item),
                }
            )

    return groups


def author_to_cv_name(author):
    """Format one BibTeX author name for the CV."""
    author = bibtex_to_plain(author)
    parts = [part.strip() for part in author.split(",")]
    if len(parts) == 2:
        name = f"{parts[1]} {parts[0]}".strip()
    elif len(parts) >= 3:
        name = f"{parts[2]} {parts[0]}, {parts[1]}".strip()
    else:
        name = author.strip()

    compact = re.sub(r"[^a-z]", "", name.lower())
    if compact == "jakewliu":
        return r"\name"
    return latex_escape_text(name)


def join_cv_authors(authors):
    """Join CV author names with the CV's Oxford-comma style."""
    if not authors:
        return ""
    if len(authors) == 1:
        return authors[0]
    if len(authors) == 2:
        delimiter = r"\ and " if authors[0] == r"\name" else " and "
        return authors[0] + delimiter + authors[1]
    return ", ".join(authors[:-1]) + ", and " + authors[-1]


def format_cv_authors(fields):
    """Format BibTeX authors for a CV item."""
    authors = [author_to_cv_name(author) for author in re.split(r"\s+and\s+", fields.get("author", "")) if author.strip()]
    return join_cv_authors(authors)


def cv_date(fields):
    """Format publication month and year for the CV."""
    year = fields.get("year", "").strip("{}")
    month = month_number(fields.get("month"))
    if month and year:
        return f"{MONTH_LABELS[month]} {year}"
    return year


def format_cv_pages(pages):
    """Format pages with singular/plural labels."""
    pages = normalize_pages(pages)
    label = "pp." if re.search(r"\d\s*--\s*\d", pages) else "p."
    return f"{label} {latex_escape_text(pages)}"


def cv_field_details(fields, include_location=False):
    """Format volume, number, pages, location, and date details."""
    details = []
    if fields.get("volume"):
        details.append(f"vol. {latex_escape_text(fields['volume'])}")
    if fields.get("number"):
        details.append(f"no. {latex_escape_text(normalize_pages(fields['number']))}")
    if fields.get("pages"):
        details.append(format_cv_pages(fields["pages"]))
    if include_location and fields.get("location"):
        details.append(latex_escape_text(fields["location"]))
    date_text = cv_date(fields)
    if date_text:
        details.append(date_text)
    return details


def linked_title(fields):
    """Return the publication title, linked to DOI or URL when available."""
    title = latex_escape_text(fields.get("title", ""))
    url = ""
    if fields.get("doi"):
        url = f"https://doi.org/{normalize_doi(fields['doi'])}"
    elif fields.get("url"):
        url = fields["url"]
    if not url:
        return title
    return rf"\href{{{latex_escape_url(url)}}}{{{title}}}"


def doi_suffix(fields):
    """Return a CV DOI suffix for entries with DOI metadata."""
    doi = normalize_doi(fields.get("doi", ""))
    return rf" \pubdoi{{{doi}}}." if doi else ""


def render_book_cv_item(fields):
    """Render a BibTeX book entry as a CV item."""
    authors = format_cv_authors(fields)
    title = linked_title(fields)
    details = []
    if fields.get("publisher"):
        details.append(latex_escape_text(fields["publisher"]))
    date_text = cv_date(fields)
    if date_text:
        details.append(date_text)

    sentence = f"{authors}. " if authors else ""
    sentence += rf"\textit{{{title}}}"
    if details:
        sentence += f". {', '.join(details)}"
    if fields.get("isbn"):
        sentence += f". ISBN {latex_escape_text(fields['isbn'])}"
    sentence += doi_suffix(fields) if fields.get("doi") else "."
    return f"  \\item {sentence}"


def render_journal_cv_item(fields):
    """Render a BibTeX journal article as a CV item."""
    authors = format_cv_authors(fields)
    title = linked_title(fields)
    journal = latex_escape_text(fields.get("journal", ""))
    details = [rf"\textit{{{journal}}}"] if journal else []
    details.extend(cv_field_details(fields))
    tail = f" {', '.join(details)}." if details else ""
    return f"  \\item {authors}. ``{title}.''{tail}{doi_suffix(fields)}"


def render_conference_cv_item(fields):
    """Render a BibTeX conference paper as a CV item."""
    authors = format_cv_authors(fields)
    title = linked_title(fields)
    booktitle = latex_escape_text(fields.get("booktitle", ""))
    details = cv_field_details(fields, include_location=True)
    venue = rf"In \textit{{{booktitle}}}" if booktitle else "In"
    if details:
        venue += f", {', '.join(details)}"
    return f"  \\item {authors}. ``{title}.'' {venue}.{doi_suffix(fields)}"


def render_cv_item(publication):
    """Render one parsed bibliography publication as a CV item."""
    group = publication["group"]
    fields = publication["fields"]
    if group == "book":
        return render_book_cv_item(fields)
    if group == "conference":
        return render_conference_cv_item(fields)
    return render_journal_cv_item(fields)


def read_bib_publications():
    """Read all BibTeX publications needed for the CV."""
    with open(BIB_FILE) as f:
        content = f.read()

    publications = []
    for index, entry in enumerate(iter_bibtex_entries(content)):
        parsed = parse_bibtex_entry(entry)
        if not parsed:
            continue
        entry_type, key, fields = parsed
        group = entry_group(entry_type)
        publications.append(
            {
                "entry_type": entry_type,
                "key": key,
                "fields": fields,
                "group": group,
                "index": index,
                "doi": doi_from_fields(fields),
                "title": normalize_title(bibtex_to_plain(fields.get("title", ""))),
            }
        )
    return publications


def matching_existing_item(publication, existing_items, used_existing):
    """Find a matching existing CV item by DOI first, then normalized title."""
    doi = publication["doi"]
    if doi:
        for index, existing in enumerate(existing_items):
            if index not in used_existing and doi in existing["dois"]:
                used_existing.add(index)
                return existing["item"]

    title = publication["title"]
    if title:
        for index, existing in enumerate(existing_items):
            if index not in used_existing and title == existing["title"]:
                used_existing.add(index)
                return existing["item"]
    return None


def build_cv_publications_section(publications, existing_groups):
    """Build the full CV Publications section from bibliography metadata."""
    by_group = {group: [] for group, _, _ in CV_GROUPS}
    for publication in publications:
        by_group[publication["group"]].append(publication)

    lines = [r"\section*{Publications}"]
    generated_count = 0

    for group, title, label in CV_GROUPS:
        lines.extend(["", rf"\subsection*{{{title}}}", rf"\begin{{enumerate}}[label={{[{label}\arabic*]}}]"])

        used_existing = set()
        item_lines = []
        for publication in sorted(by_group[group], key=publication_sort_key):
            existing_item = matching_existing_item(publication, existing_groups[group], used_existing)
            if existing_item:
                item_lines.append(existing_item)
            else:
                item_lines.append(render_cv_item(publication))
                generated_count += 1

        for index, existing in enumerate(existing_groups[group]):
            if index not in used_existing:
                item_lines.append(existing["item"])

        if item_lines:
            lines.append("\n\n".join(item_lines))
        lines.append(r"\end{enumerate}")

    return "\n".join(lines), generated_count


def today_label():
    """Return today's date in the CV header style."""
    today = date.today()
    return f"{FULL_MONTH_LABELS[today.month]} {today.day}, {today.year}"


def sync_cv_publications():
    """Sync cv/Jake_W_Liu_CV.tex Publications from _bibliography/papers.bib."""
    with open(CV_FILE) as f:
        cv_content = f.read()

    start_match = re.search(r"\\section\*\{Publications\}", cv_content)
    if not start_match:
        raise RuntimeError(f"Could not find Publications section in {CV_FILE}")

    end_match = re.search(r"\n\\end\{document\}", cv_content[start_match.start() :])
    if not end_match:
        raise RuntimeError(f"Could not find \\end{{document}} after Publications section in {CV_FILE}")

    section_start = start_match.start()
    section_end = section_start + end_match.start()
    existing_groups = parse_existing_cv_publications(cv_content)
    publications = read_bib_publications()
    new_section, generated_count = build_cv_publications_section(publications, existing_groups)
    updated = cv_content[:section_start] + new_section + "\n\n" + cv_content[section_end:].lstrip("\n")

    if updated != cv_content:
        updated = re.sub(r"Last updated: [^\n]+", f"Last updated: {today_label()}", updated, count=1)
        with open(CV_FILE, "w") as f:
            f.write(updated)
        return True, generated_count
    return False, generated_count


def main():
    add_mode = "--add" in sys.argv
    sync_cv_mode = "--sync-cv" in sys.argv

    if sync_cv_mode and not add_mode:
        changed, generated_count = sync_cv_publications()
        if changed:
            print(f"Updated cv/Jake_W_Liu_CV.tex ({generated_count} generated item(s)).")
        else:
            print("cv/Jake_W_Liu_CV.tex is already synced.")
        return

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
        if add_mode:
            changed, generated_count = sync_cv_publications()
            if changed:
                print(f"Updated cv/Jake_W_Liu_CV.tex ({generated_count} generated item(s)).")
            else:
                print("cv/Jake_W_Liu_CV.tex is already synced.")
        return

    print(f"--- {len(missing)} missing publication(s) ---\n")

    added_count = 0
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
                changed, generated_count = sync_cv_publications()
                if changed:
                    print(f"Updated cv/Jake_W_Liu_CV.tex ({generated_count} generated item(s)).")
                print("Quit.")
                return
            elif answer == "y":
                with open(BIB_FILE, "a") as f:
                    f.write("\n" + bib + "\n")
                existing_keys.add(key.lower())
                added_count += 1
                print("  -> Added!\n")
            else:
                print("  -> Skipped.\n")
        else:
            print()

    if add_mode:
        changed, generated_count = sync_cv_publications()
        if changed:
            print(f"Updated cv/Jake_W_Liu_CV.tex ({generated_count} generated item(s)).")
        elif added_count:
            print("cv/Jake_W_Liu_CV.tex is already synced.")

    if not add_mode and missing:
        print("Run with --add to interactively add missing publications:")
        print(f"  python3 bin/find_pubs.py --add")


if __name__ == "__main__":
    main()
