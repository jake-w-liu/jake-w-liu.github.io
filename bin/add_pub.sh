#!/bin/bash
# Usage: ./bin/add_pub.sh <DOI>
# Example: ./bin/add_pub.sh 10.1016/j.rio.2026.100990
#
# Fetches BibTeX from CrossRef, adds site conventions, and appends to papers.bib.

BIB_FILE="$(dirname "$0")/../_bibliography/papers.bib"
DOI="${1}"

if [ -z "$DOI" ]; then
  echo "Usage: $0 <DOI>"
  echo "Example: $0 10.1016/j.rio.2026.100990"
  exit 1
fi

# Strip URL prefix if full URL was given
DOI="${DOI#https://doi.org/}"
DOI="${DOI#http://doi.org/}"

echo "Fetching BibTeX for DOI: $DOI ..."
BIB=$(curl -sLH "Accept: application/x-bibtex" "https://doi.org/$DOI")

if [ -z "$BIB" ] || echo "$BIB" | grep -q "Resource not found"; then
  echo "Error: Could not fetch BibTeX for DOI: $DOI"
  exit 1
fi

# Detect entry type for default abbr
if echo "$BIB" | head -1 | grep -qi "@inproceedings\|@incollection"; then
  DEFAULT_ABBR="Proceedings"
elif echo "$BIB" | head -1 | grep -qi "@book"; then
  DEFAULT_ABBR="Book"
else
  DEFAULT_ABBR="Journal"
fi

# Add abbr and url fields before the closing brace
BIB=$(echo "$BIB" | sed "s|}$|,\n\tabbr = {$DEFAULT_ABBR},\n\turl = {https://doi.org/$DOI},\n}|")

echo ""
echo "========== BibTeX Entry =========="
echo "$BIB"
echo "=================================="
echo ""
read -p "Add this entry to papers.bib? [y/N] " CONFIRM

if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
  echo "" >> "$BIB_FILE"
  echo "$BIB" >> "$BIB_FILE"
  echo ""
  echo "Added to $BIB_FILE"
else
  echo "Cancelled."
fi
