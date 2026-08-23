import importlib.util
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
import unittest


SCRIPT_PATH = Path(__file__).parents[1] / "bin" / "update_publication_metadata.py"
SPEC = importlib.util.spec_from_file_location("update_publication_metadata", SCRIPT_PATH)
publication_metadata = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publication_metadata)


ARXIV_RESPONSE = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <arxiv:doi>10.1000/example</arxiv:doi>
  </entry>
</feed>
"""

CROSSREF_RESPONSE = b'''{
  "status": "ok",
  "message": {
    "type": "journal-article",
    "title": ["A Carefully Tested Paper"],
    "container-title": ["Journal of Tests"],
    "volume": "42",
    "issue": "3",
    "page": "10--20",
    "publisher": "Test Publisher",
    "published-print": {"date-parts": [[2025]]}
  }
}'''


class PublicationMetadataUpdateTests(unittest.TestCase):
    def test_updates_an_arxiv_preprint_from_matching_crossref_metadata(self):
        bibliography = """@article{example2023,
  abbr = {arXiv},
  author = {Example, Ada and Tester, Pat},
  title = {A Carefully Tested Paper},
  journal = {arXiv preprint arXiv:2302.11474},
  year = {2023},
  arxiv = {2302.11474}
}
"""

        def fetch(url):
            if "export.arxiv.org" in url:
                return ARXIV_RESPONSE
            if "api.crossref.org" in url:
                return CROSSREF_RESPONSE
            self.fail(f"Unexpected URL: {url}")

        updated, changes = publication_metadata.update_bibliography(bibliography, fetch)

        self.assertEqual(changes, ["example2023"])
        self.assertIn("abbr = {arXiv}", updated)
        self.assertIn("journal = {Journal of Tests}", updated)
        self.assertIn("volume = {42}", updated)
        self.assertIn("number = {3}", updated)
        self.assertIn("pages = {10--20}", updated)
        self.assertIn("publisher = {Test Publisher}", updated)
        self.assertIn("year = {2025}", updated)
        self.assertIn("doi = {10.1000/example}", updated)
        self.assertIn("arxiv = {2302.11474}", updated)

    def test_does_not_update_when_crossref_title_does_not_match(self):
        bibliography = """@article{example2023,
  title = {A Carefully Tested Paper},
  journal = {arXiv preprint arXiv:2302.11474},
  year = {2023},
  arxiv = {2302.11474}
}
"""
        mismatched_crossref_response = CROSSREF_RESPONSE.replace(
            b"A Carefully Tested Paper", b"A Different Paper"
        )

        def fetch(url):
            if "export.arxiv.org" in url:
                return ARXIV_RESPONSE
            if "api.crossref.org" in url:
                return mismatched_crossref_response
            self.fail(f"Unexpected URL: {url}")

        updated, changes = publication_metadata.update_bibliography(bibliography, fetch)

        self.assertEqual(updated, bibliography)
        self.assertEqual(changes, [])

    def test_does_not_update_a_non_journal_crossref_record(self):
        bibliography = """@article{example2023,
  title = {A Carefully Tested Paper},
  journal = {arXiv preprint arXiv:2302.11474},
  year = {2023},
  arxiv = {2302.11474}
}
"""
        proceedings_response = CROSSREF_RESPONSE.replace(
            b'"journal-article"', b'"proceedings-article"'
        )

        def fetch(url):
            if "export.arxiv.org" in url:
                return ARXIV_RESPONSE
            if "api.crossref.org" in url:
                return proceedings_response
            self.fail(f"Unexpected URL: {url}")

        updated, changes = publication_metadata.update_bibliography(bibliography, fetch)

        self.assertEqual(updated, bibliography)
        self.assertEqual(changes, [])

    def test_escapes_braces_in_crossref_metadata(self):
        bibliography = """@article{example2023,
  title = {A Carefully Tested Paper},
  journal = {arXiv preprint arXiv:2302.11474},
  year = {2023},
  arxiv = {2302.11474}
}
"""
        special_character_response = CROSSREF_RESPONSE.replace(
            b"Test Publisher", b"Test {Publisher}"
        )

        def fetch(url):
            if "export.arxiv.org" in url:
                return ARXIV_RESPONSE
            if "api.crossref.org" in url:
                return special_character_response
            self.fail(f"Unexpected URL: {url}")

        updated, changes = publication_metadata.update_bibliography(bibliography, fetch)

        self.assertEqual(changes, ["example2023"])
        self.assertIn(r"publisher = {Test \{Publisher\}}", updated)

    def test_leaves_an_entry_unchanged_when_crossref_returns_malformed_json(self):
        bibliography = """@article{example2023,
  title = {A Carefully Tested Paper},
  journal = {arXiv preprint arXiv:2302.11474},
  year = {2023},
  arxiv = {2302.11474}
}
"""

        def fetch(url):
            if "export.arxiv.org" in url:
                return ARXIV_RESPONSE
            if "api.crossref.org" in url:
                return b"{"
            self.fail(f"Unexpected URL: {url}")

        error_output = StringIO()
        with redirect_stderr(error_output):
            updated, changes = publication_metadata.update_bibliography(bibliography, fetch)

        self.assertEqual(updated, bibliography)
        self.assertEqual(changes, [])
        self.assertIn("metadata could not be read", error_output.getvalue())

    def test_leaves_the_current_bibliography_unchanged_without_an_arxiv_doi(self):
        bibliography = (Path(__file__).parents[1] / "_bibliography" / "papers.bib").read_text()

        def fetch(url):
            self.assertIn("export.arxiv.org", url)
            return b"<feed xmlns=\"http://www.w3.org/2005/Atom\" />"

        updated, changes = publication_metadata.update_bibliography(bibliography, fetch)

        self.assertEqual(updated, bibliography)
        self.assertEqual(changes, [])


if __name__ == "__main__":
    unittest.main()
