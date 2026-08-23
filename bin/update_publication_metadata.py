#!/usr/bin/env python3
"""Update published metadata for arXiv preprints in a BibTeX bibliography.

The script only updates entries that still identify themselves as arXiv
preprints and whose arXiv record exposes a DOI. Crossref is then used as the
canonical source for the journal metadata. It is designed to be run by GitHub
Actions, which proposes any edits in a pull request for review.
"""

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher
from pathlib import Path


ARXIV_API_URL = "https://export.arxiv.org/api/query?id_list={}"
CROSSREF_API_URL = "https://api.crossref.org/works/{}"
ARXIV_NAMESPACE = "http://arxiv.org/schemas/atom"
TITLE_MATCH_THRESHOLD = 0.95


def fetch_url(url):
    """Fetch a URL with a descriptive user agent for public metadata APIs."""
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "rileyjmurray.github.io publication metadata updater"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read()


def normalize_value(value):
    """Return the plain value from a simple BibTeX field value."""
    value = value.strip()
    if len(value) >= 2 and value[0] == "{" and value[-1] == "}":
        return value[1:-1].strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1].strip()
    return value


def normalized_title(title):
    """Normalize title punctuation and case before comparing metadata sources."""
    return "".join(character for character in title.casefold() if character.isalnum())


def title_matches(bibtex_title, crossref_title):
    """Require a very close title match before changing an entry."""
    return (
        SequenceMatcher(
            None, normalized_title(bibtex_title), normalized_title(crossref_title)
        ).ratio()
        >= TITLE_MATCH_THRESHOLD
    )


def split_entries(bibliography):
    """Yield text segments, preserving the exact spacing between BibTeX entries."""
    cursor = 0
    for match in re.finditer(r"@\w+\s*\{", bibliography):
        start = match.start()
        if start < cursor:
            continue
        opening_brace = bibliography.find("{", start)
        depth = 0
        end = None
        for index in range(opening_brace, len(bibliography)):
            if bibliography[index] == "{":
                depth += 1
            elif bibliography[index] == "}":
                depth -= 1
                if depth == 0:
                    end = index + 1
                    break
        if end is None:
            raise ValueError("Unclosed BibTeX entry")
        yield bibliography[cursor:start], bibliography[start:end]
        cursor = end
    yield bibliography[cursor:], None


FIELD_PATTERN = re.compile(r"^(?P<indent>\s*)(?P<name>[\w-]+)\s*=\s*(?P<value>.*)$")


def fields_in(entry):
    """Read single-line BibTeX fields used by the site's bibliography."""
    fields = {}
    for index, line in enumerate(entry.splitlines()):
        match = FIELD_PATTERN.match(line)
        if not match:
            continue
        value = match.group("value").strip()
        if value.endswith(","):
            value = value[:-1].rstrip()
        fields[match.group("name").casefold()] = (index, normalize_value(value))
    return fields


def arxiv_doi(arxiv_id, fetch):
    """Return the DOI supplied by arXiv, if the preprint has one."""
    response = fetch(ARXIV_API_URL.format(urllib.parse.quote(arxiv_id, safe=".")))
    document = ET.fromstring(response)
    doi = document.findtext(f".//{{{ARXIV_NAMESPACE}}}doi")
    return doi.strip() if doi else None


def crossref_record(doi, fetch):
    """Fetch Crossref's canonical metadata for a DOI."""
    response = fetch(CROSSREF_API_URL.format(urllib.parse.quote(doi, safe="")))
    return json.loads(response)["message"]


def crossref_year(record):
    """Prefer the printed date, then online and issued dates, for display."""
    for field in ("published-print", "published-online", "issued"):
        parts = record.get(field, {}).get("date-parts", [[]])
        if parts and parts[0]:
            return str(parts[0][0])
    return None


def set_field(lines, name, value):
    """Replace a field or append it while preserving the entry's basic layout."""
    pattern = re.compile(rf"^(?P<indent>\s*){re.escape(name)}\s*=\s*.*$")
    for index, line in enumerate(lines):
        match = pattern.match(line)
        if match:
            lines[index] = f"{match.group('indent')}{name} = {{{value}}},"
            return

    for index in range(len(lines) - 1, -1, -1):
        if FIELD_PATTERN.match(lines[index]):
            if not lines[index].rstrip().endswith(","):
                lines[index] = f"{lines[index].rstrip()},"
            lines.insert(index + 1, f"  {name} = {{{value}}},")
            return
    raise ValueError("BibTeX entry has no field to append after")


def remove_field(lines, name):
    """Remove a field without changing unrelated entry content."""
    pattern = re.compile(rf"^\s*{re.escape(name)}\s*=")
    lines[:] = [line for line in lines if not pattern.match(line)]


def update_entry(entry, fetch):
    """Update one eligible BibTeX entry and return its citation key when changed."""
    header = re.match(r"@(\w+)\s*\{\s*([^,]+),", entry)
    if not header or header.group(1).casefold() != "article":
        return entry, None

    key = header.group(2).strip()
    fields = fields_in(entry)
    arxiv = fields.get("arxiv")
    journal = fields.get("journal")
    title = fields.get("title")
    if not arxiv or not journal or not title:
        return entry, None
    if not journal[1].casefold().startswith("arxiv preprint"):
        return entry, None

    doi = arxiv_doi(arxiv[1], fetch)
    if not doi:
        return entry, None
    record = crossref_record(doi, fetch)
    crossref_titles = record.get("title", [])
    crossref_title = crossref_titles[0] if crossref_titles else ""
    if not crossref_title or not title_matches(title[1], crossref_title):
        return entry, None

    journal_titles = record.get("container-title", [])
    if not journal_titles:
        return entry, None

    lines = entry.splitlines()
    set_field(lines, "journal", journal_titles[0])
    set_field(lines, "doi", doi)

    for field, crossref_field in (
        ("volume", "volume"),
        ("number", "issue"),
        ("pages", "page"),
        ("publisher", "publisher"),
    ):
        value = record.get(crossref_field)
        if value:
            set_field(lines, field, str(value))

    year = crossref_year(record)
    if year:
        set_field(lines, "year", year)

    abbr = fields.get("abbr")
    if abbr and abbr[1].casefold() == "arxiv":
        remove_field(lines, "abbr")

    return "\n".join(lines), key


def update_bibliography(bibliography, fetch=fetch_url):
    """Return an updated bibliography and the keys changed by this run."""
    output = []
    changes = []
    for prefix, entry in split_entries(bibliography):
        output.append(prefix)
        if entry is None:
            continue
        try:
            updated_entry, key = update_entry(entry, fetch)
        except (ET.ParseError, KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as error:
            print(f"Skipping an entry because metadata could not be read: {error}", file=sys.stderr)
            updated_entry, key = entry, None
        output.append(updated_entry)
        if key:
            changes.append(key)
    return "".join(output), changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bibliography",
        type=Path,
        default=Path("_bibliography/papers.bib"),
        help="BibTeX file to update (default: _bibliography/papers.bib)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Report eligible changes without writing them"
    )
    arguments = parser.parse_args()

    bibliography = arguments.bibliography.read_text()
    updated, changes = update_bibliography(bibliography)
    if not changes:
        print("No publication metadata updates found.")
        return

    print(f"Updated publication metadata for: {', '.join(changes)}")
    if not arguments.dry_run:
        arguments.bibliography.write_text(updated)


if __name__ == "__main__":
    main()
