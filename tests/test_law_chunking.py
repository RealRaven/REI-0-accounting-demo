from app.core.rag.chunking import chunk_law_text, chunk_text


def test_chunk_law_by_paragraph():
    text = "§ 15 UStG Vorsteuer\nAbs. 1 ...\n\n§ 4 EStG Betriebsausgaben\n..."
    chunks = chunk_law_text(text, pdf_path="estg.pdf")
    paras = [c["para"] for c in chunks]
    assert "§ 15" in paras or any("15" in p for p in paras)


def test_chunk_text_small_input():
    assert chunk_text("hello") == ["hello"]
    assert chunk_text("") == []