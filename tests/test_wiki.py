from pathlib import Path

from zvec_mcp.wiki import (
    backlinks_for,
    build_navigation_index,
    extract_wikilinks,
    navigate_file,
    resolve_wikilink,
    retrieve_wikilink,
    write_navigation_index,
)


def test_extract_wikilinks_with_label_and_heading() -> None:
    links = extract_wikilinks("See [[people/randy-daal|Randy]] and [[topic#Part]].")

    assert [link.target for link in links] == ["people/randy-daal", "topic"]
    assert links[0].label == "Randy"
    assert links[1].heading == "Part"


def test_resolve_wikilink_from_wiki_root(tmp_path: Path) -> None:
    root = tmp_path / "wiki"
    source = root / "projects" / "upgraide.md"
    target = root / "people" / "randy-daal.md"
    source.parent.mkdir(parents=True)
    target.parent.mkdir(parents=True)
    (root / "_index.md").write_text("# Index", encoding="utf-8")
    source.write_text("[[people/randy-daal]]", encoding="utf-8")
    target.write_text("# Randy", encoding="utf-8")

    resolved = resolve_wikilink(source, "[[people/randy-daal]]")

    assert resolved["exists"] is True
    assert resolved["resolved_path"] == str(target.resolve())


def test_navigate_file_uses_existing_backlinks_json(tmp_path: Path) -> None:
    root = tmp_path / "wiki"
    source = root / "people" / "randy-daal.md"
    referrer = root / "projects" / "upgraide.md"
    source.parent.mkdir(parents=True)
    referrer.parent.mkdir(parents=True)
    source.write_text("# Randy\n[[projects/upgraide]]", encoding="utf-8")
    referrer.write_text("[[people/randy-daal]]", encoding="utf-8")
    (root / "_backlinks.json").write_text(
        '{"people/randy-daal.md": ["projects/upgraide.md"]}',
        encoding="utf-8",
    )

    result = navigate_file(source)

    assert result["backlinks"] == [str(referrer.resolve())]
    assert result["outgoing"][0]["exists"] is True


def test_sidecar_backlinks_for_generic_tree(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    source = root / "a.md"
    target = root / "b.md"
    source.parent.mkdir()
    source.write_text("[[b]]", encoding="utf-8")
    target.write_text("# B", encoding="utf-8")
    sidecar = tmp_path / "nav.json"

    index = build_navigation_index(root)
    write_navigation_index(index, sidecar)

    assert backlinks_for(target, sidecar) == [str(source.resolve())]


def test_retrieve_wikilink_reads_target_content(tmp_path: Path) -> None:
    root = tmp_path / "wiki"
    source = root / "source.md"
    target = root / "target.md"
    root.mkdir()
    (root / "_index.md").write_text("# Index", encoding="utf-8")
    source.write_text("[[target]]", encoding="utf-8")
    target.write_text("# Target", encoding="utf-8")

    result = retrieve_wikilink(source, "[[target]]")

    assert result["exists"] is True
    assert result["content"] == "# Target"
