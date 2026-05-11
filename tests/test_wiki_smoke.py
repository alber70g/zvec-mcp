from pathlib import Path

import zvec

from zvec_mcp.config import Config
from zvec_mcp.knowledge import KnowledgeBase
from zvec_mcp.wiki import backlinks_for, navigate_file, retrieve_wikilink


class FakeEmbedder:
    dim = 4

    def embed(self, text: str) -> list[float]:
        value = float(len(text) % 10) / 10.0
        return [value, 0.0, 0.0, 1.0]


def test_wiki_smoke_ingest_search_and_navigate(tmp_path: Path) -> None:
    zvec.init()
    root = tmp_path / "wiki"
    root.mkdir()
    source = root / "a.md"
    target = root / "b.md"
    source.write_text("# A\nSee [[b]].\nAlpha project notes.", encoding="utf-8")
    target.write_text("# B\nBacklink target.", encoding="utf-8")

    cfg = Config(data_dir=tmp_path / "data")
    kb = KnowledgeBase(cfg, FakeEmbedder())  # type: ignore[arg-type]

    ingest_result = kb.ingest_path(str(root))
    search_result = kb.search("alpha", topk=2)
    nav_result = navigate_file(source, cfg.navigation_index_path)
    retrieve_result = retrieve_wikilink(source, "[[b]]")
    backlinks_result = backlinks_for(target, cfg.navigation_index_path)

    assert ingest_result["files_ingested"] == 2
    assert ingest_result["chunks_stored"] == 2
    assert len(search_result) >= 1
    assert nav_result["outgoing"][0]["resolved_path"] == str(target.resolve())
    assert retrieve_result["content"] == "# B\nBacklink target."
    assert backlinks_result == [str(source.resolve())]
