"""Publish docs/motherduck_guide.md to MotherDuck as a Guide, so tools that connect through MotherDuck read it.

Run it with:  uv run python -m analyst.publish_guide --dry-run    (shows what would happen, changes nothing)
              uv run python -m analyst.publish_guide              (creates the Guide, or adds a new version)

The repo file is the master copy. Only the text below its first "---" line is published; the part above is a
note for the repo. MotherDuck Guides cannot be created in the web UI, only with SQL (MD_CREATE_GUIDE) or the MCP
tools, which this project blocks. This uses the normal MotherDuck connection (the motherduck_token variable).
"""

import argparse
import pathlib

from ingest.raw_loader import connect

GUIDE_FILE = pathlib.Path(__file__).resolve().parent.parent / "docs" / "motherduck_guide.md"
TITLE = "NHL database: definitions and pitfalls"
TOPIC = "nhl"
DESCRIPTION = "Scope, definitions, coverage and common mistakes for questions about the nhl database."
ACCESS = "user"  # private to the owner (decided 2026-10-15); 'organization' needs admin rights


def guide_text(path=GUIDE_FILE):
    """The part of the file below its first line that is exactly '---'."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if "---" not in lines:
        raise ValueError(f"{path.name} has no '---' line separating the repo note from the guide")
    body = "\n".join(lines[lines.index("---") + 1:]).strip()
    if not body:
        raise ValueError(f"{path.name} has nothing below its '---' line")
    return body + "\n"


def existing_guide_id(con):
    """The ID of our Guide if it already exists (same topic and title), else None."""
    row = con.execute(
        "SELECT id FROM MD_LIST_GUIDES(topic = ?) WHERE title = ? ORDER BY updated_at DESC LIMIT 1",
        [TOPIC, TITLE],
    ).fetchone()
    return row[0] if row else None


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="show what would happen without changing anything")
    parser.add_argument("--comment", default="Published from docs/motherduck_guide.md", help="note for this version")
    args = parser.parse_args()

    content = guide_text()
    con = connect()
    try:
        guide_id = existing_guide_id(con)
        action = f"add a new version to Guide {guide_id}" if guide_id else "create a new Guide"
        print(f"{TITLE!r} (topic {TOPIC}, access {ACCESS}): {len(content):,} characters. "
              f"{'Would' if args.dry_run else 'Going to'} {action}.")
        if args.dry_run:
            print("Dry run: nothing changed.")
            return
        if guide_id:
            row = con.execute(
                "SELECT id, current_version FROM MD_UPDATE_GUIDE(id = ?, content = ?, change_comment = ?)",
                [guide_id, content, args.comment],
            ).fetchone()
        else:
            row = con.execute(
                "SELECT id, current_version FROM MD_CREATE_GUIDE(title = ?, content = ?, topic = ?, "
                "description = ?, access = ?, change_comment = ?)",
                [TITLE, content, TOPIC, DESCRIPTION, ACCESS, args.comment],
            ).fetchone()
        print(f"Done: Guide {row[0]}, version {row[1]}.")
    finally:
        con.close()


if __name__ == "__main__":
    main()
