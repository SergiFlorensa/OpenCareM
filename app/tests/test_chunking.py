from app.core.chunking import SemanticChunker


def test_semantic_chunker_splits_oversized_paragraph_with_overlap():
    chunker = SemanticChunker(
        token_counter=lambda text: len(text.split()),
        chunk_size_tokens=20,
        overlap_tokens=5,
    )
    content = (
        "# Nefrologia\n"
        "Paciente con oliguria persistente y elevacion progresiva de creatinina "
        "con hiperpotasemia severa y riesgo electrico en el electrocardiograma. "
        "Se requiere monitorizacion estrecha y reevaluacion seriada de perfusion."
    )

    chunks = chunker.chunk(content=content, title="Guia nefrologia", specialty="nephrology")

    assert len(chunks) >= 2
    first_tail = chunks[0].text.split()[-5:]
    second_head = chunks[1].text.split()[:10]
    assert any(token in second_head for token in first_tail)


def test_semantic_chunker_keeps_chunk_size_bounded_on_large_single_block():
    chunker = SemanticChunker(
        token_counter=lambda text: len(text.split()),
        chunk_size_tokens=32,
        overlap_tokens=4,
    )
    very_long_line = " ".join(["hiperkalemia"] * 120)
    content = f"# Oncologia\n{very_long_line}"

    chunks = chunker.chunk(content=content, title="Guia onco", specialty="oncology")

    assert len(chunks) > 2
    # Margen por overlap y cabeceras; evita chunks descontrolados.
    assert all(len(chunk.text.split()) <= 42 for chunk in chunks)


def test_chunker_generates_non_placeholder_custom_questions():
    chunker = SemanticChunker(
        token_counter=lambda text: len(text.split()),
        chunk_size_tokens=64,
        overlap_tokens=8,
    )
    content = (
        "# Nefrologia\n"
        "## Hiperkalemia en urgencias\n"
        "Ante hiperkalemia con QRS ancho se recomienda calcio intravenoso, "
        "monitorizacion ECG continua y valoracion de dialisis urgente."
    )

    chunks = chunker.chunk(content=content, title="Guia nefrologia", specialty="nephrology")

    assert chunks
    first_questions = chunks[0].custom_questions
    assert first_questions
    assert all("fragmento" not in question.lower() for question in first_questions)


def test_semantic_chunker_accepts_parsed_blocks_with_content_types():
    chunker = SemanticChunker(
        token_counter=lambda text: len(text.split()),
        chunk_size_tokens=80,
        overlap_tokens=8,
    )
    parsed_blocks = [
        {
            "type": "table",
            "content": "| lactato | 4.2 |",
            "section_path": "Documento > Tabla sepsis",
        },
        {
            "type": "formula",
            "content": "$$ dosis = peso * 0.1 $$",
            "section_path": "Documento > Formula dosis",
        },
    ]

    chunks = chunker.chunk(
        content="contenido fallback",
        title="Guia sepsis",
        specialty="sepsis",
        parsed_blocks=parsed_blocks,
    )

    assert chunks
    content_types = {chunk.content_type.value for chunk in chunks}
    assert "table" in content_types or "code_block" in content_types
