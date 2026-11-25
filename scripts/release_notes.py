"""Read the matching changelog section for a release tag."""
import re
import sys

from build import ROOT


def notes(tag):
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise ValueError("Expected a vMAJOR.MINOR.PATCH release tag")
    text = (ROOT / "CHANGELOG.md").read_text()
    pattern = rf"^## \[{re.escape(tag[1:])}\] - \d{{4}}-\d{{2}}-\d{{2}}\n(.+?)(?=^## |\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    if not match or not match[1].strip():
        raise ValueError(f"Missing changelog entry for {tag}")
    return match[1].strip()


if __name__ == "__main__":
    print(notes(sys.argv[1]))
