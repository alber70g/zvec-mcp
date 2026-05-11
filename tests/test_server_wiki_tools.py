import json
from pathlib import Path

from zvec_mcp import server


def test_knowledge_navigate_file_tool(tmp_path: Path) -> None:
    root = tmp_path / "wiki"
    source = root / "a.md"
    target = root / "b.md"
    root.mkdir()
    (root / "_index.md").write_text("# Index", encoding="utf-8")
    source.write_text("[[b]]", encoding="utf-8")
    target.write_text("# B", encoding="utf-8")

    result = json.loads(server.knowledge_navigate_file(str(source)))

    assert result["status"] == "ok"
    assert result["outgoing"][0]["resolved_path"] == str(target.resolve())


def test_knowledge_wikilink_retrieve_tool(tmp_path: Path) -> None:
    root = tmp_path / "wiki"
    source = root / "a.md"
    target = root / "b.md"
    root.mkdir()
    (root / "_index.md").write_text("# Index", encoding="utf-8")
    source.write_text("[[b]]", encoding="utf-8")
    target.write_text("# B", encoding="utf-8")

    result = json.loads(server.knowledge_wikilink_retrieve(str(source), "[[b]]"))

    assert result["status"] == "ok"
    assert result["content"] == "# B"


def test_knowledge_backlinks_tool(tmp_path: Path) -> None:
    root = tmp_path / "wiki"
    source = root / "a.md"
    referrer = root / "b.md"
    root.mkdir()
    source.write_text("# A", encoding="utf-8")
    referrer.write_text("[[a]]", encoding="utf-8")
    (root / "_backlinks.json").write_text('{"a.md": ["b.md"]}', encoding="utf-8")

    result = json.loads(server.knowledge_backlinks(str(source)))

    assert result["status"] == "ok"
    assert result["backlinks"] == [str(referrer.resolve())]
