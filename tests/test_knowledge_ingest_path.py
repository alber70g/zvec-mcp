from pathlib import Path

from zvec_mcp.config import Config
from zvec_mcp.knowledge import KnowledgeBase


class FakeKnowledgeBase(KnowledgeBase):
    def __init__(self, cfg: Config) -> None:
        self._cfg = cfg
        self.ingested: list[str] = []

    def ingest_file(self, path: str) -> int:
        self.ingested.append(path)
        return 2


def test_ingest_path_ingests_matching_markdown_and_writes_navigation_index(tmp_path: Path) -> None:
    root = tmp_path / "wiki"
    root.mkdir()
    (root / "a.md").write_text("[[b]]", encoding="utf-8")
    (root / "b.md").write_text("# B", encoding="utf-8")
    (root / "skip.txt").write_text("no", encoding="utf-8")
    cfg = Config(data_dir=tmp_path / "data")
    kb = FakeKnowledgeBase(cfg)

    result = kb.ingest_path(str(root))

    assert result["files_seen"] == 2
    assert result["files_ingested"] == 2
    assert result["chunks_stored"] == 4
    assert result["failures"] == []
    assert sorted(Path(path).name for path in kb.ingested) == ["a.md", "b.md"]
    assert cfg.navigation_index_path.is_file()


def test_ingest_path_honors_max_files(tmp_path: Path) -> None:
    root = tmp_path / "wiki"
    root.mkdir()
    (root / "a.md").write_text("A", encoding="utf-8")
    (root / "b.md").write_text("B", encoding="utf-8")
    kb = FakeKnowledgeBase(Config(data_dir=tmp_path / "data"))

    result = kb.ingest_path(str(root), max_files=1)

    assert result["files_seen"] == 1
    assert result["files_ingested"] == 1
    assert len(kb.ingested) == 1
