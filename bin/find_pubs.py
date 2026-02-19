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
    with open(BIB_FILE) as f:
        content = f.read()
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
    return dois, titles


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


def detect_abbr(bib):
    """Detect entry type and return appropriate abbr."""
    first_line = bib.strip().split("\n")[0].lower()
    if "@inproceedings" in first_line or "@incollection" in first_line:
        return "Proceedings"
    elif "@book" in first_line:
        return "Book"
    return "Journal"


def add_abbr_and_url(bib, doi):
    """Add abbr and url fields to a BibTeX entry."""
    abbr = detect_abbr(bib)
    # Insert before closing brace
    bib = bib.rstrip().rstrip("}")
    bib += f",\n\tabbr = {{{abbr}}},\n\turl = {{https://doi.org/{doi}}},\n}}"
    return bib


def main():
    add_mode = "--add" in sys.argv

    orcid_id = get_orcid_id()
    if not orcid_id:
        print("Error: No orcid_id found in _data/socials.yml")
        sys.exit(1)

    print(f"ORCID: {orcid_id}")
    print(f"Fetching publications from ORCID...")

    existing_dois, existing_titles = get_existing_entries()
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

            bib = add_abbr_and_url(bib, w["doi"])
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
