import time
from types import SimpleNamespace

from app.core.config import settings
from app.models.clinical_document import ClinicalDocument
from app.models.document_chunk import DocumentChunk
from app.services.rag_retriever import HybridRetriever


def test_expand_query_for_retrieval_adds_domain_terms():
    expanded_query, terms = HybridRetriever._expand_query_for_retrieval(
        "Paciente con oliguria y hiperkalemia",
        specialty_filter="nephrology",
    )

    assert expanded_query != "Paciente con oliguria y hiperkalemia"
    assert "anuria" in expanded_query
    assert "dialisis" in expanded_query
    assert len(terms) >= 2


def test_expand_query_for_retrieval_no_change_for_neutral_query():
    expanded_query, terms = HybridRetriever._expand_query_for_retrieval(
        "consulta administrativa",
        specialty_filter="general",
    )
    assert expanded_query == "consulta administrativa"
    assert terms == []


def test_boolean_term_extraction_with_explicit_operators():
    include_terms, optional_terms, exclude_terms, explicit = HybridRetriever._extract_boolean_terms(
        "neutropenia AND fiebre OR cultivos NOT pediatria"
    )

    assert explicit is True
    assert include_terms == ["neutropenia", "fiebre"]
    assert optional_terms == ["cultivos"]
    assert exclude_terms == ["pediatria"]


def test_intersect_sorted_ids_runs_in_merge_order():
    assert HybridRetriever._intersect_sorted_ids([1, 2, 4, 7], [2, 3, 4, 9]) == [2, 4]


def test_difference_sorted_ids_excludes_postings():
    assert HybridRetriever._difference_sorted_ids([1, 2, 3, 4, 8], [2, 8]) == [1, 3, 4]


def test_boolean_tokenizer_keeps_phrase_and_infers_implicit_and():
    tokens = HybridRetriever._tokenize_boolean_query('"shock septico" NOT pediatria')
    assert tokens == ['"shock septico"', "AND", "NOT", "pediatria"]


def test_boolean_rpn_respects_precedence_and_parentheses():
    tokens = HybridRetriever._tokenize_boolean_query(
        '(neutropenia OR fiebre) AND cultivos NOT pediatria'
    )
    rpn = HybridRetriever._to_rpn(tokens)
    assert rpn == ["neutropenia", "fiebre", "OR", "cultivos", "AND", "pediatria", "NOT", "AND"]


def test_levenshtein_distance_early_cutoff():
    # Distancia real > 2; el metodo corta y retorna max_distance+1.
    assert HybridRetriever._levenshtein_distance("oncologia", "xyz", max_distance=2) == 3
    assert HybridRetriever._levenshtein_distance("fiebre", "fiebre", max_distance=2) == 0


def test_boolean_tokenizer_collapses_proximity_operator():
    tokens = HybridRetriever._tokenize_boolean_query("dolor /3 pecho AND fiebre")
    assert tokens[0].startswith(HybridRetriever._NEAR_OPERAND_PREFIX)
    parsed = HybridRetriever._parse_near_operand_token(tokens[0])
    assert parsed == ("dolor", "pecho", 3)
    assert tokens[1:] == ["AND", "fiebre"]


def test_intersect_with_skips_matches_linear_intersection():
    left = list(range(10, 400, 3))
    right = list(range(20, 500, 4))
    expected = HybridRetriever._intersect_sorted_ids(left, right)
    got, shortcuts = HybridRetriever._intersect_sorted_ids_with_skips(left, right)
    assert got == expected
    assert shortcuts >= 0


def test_boolean_tokenizer_keeps_wildcard_term():
    tokens = HybridRetriever._tokenize_boolean_query("psicot* AND fiebre")
    assert tokens == ["psicot*", "AND", "fiebre"]


def test_fetch_candidate_chunks_relaxes_non_explicit_boolean_when_intersection_is_empty(
    monkeypatch,
):
    retriever = HybridRetriever()

    monkeypatch.setattr(retriever, "_ensure_sqlite_fts_index", lambda db: (True, {}))
    monkeypatch.setattr(retriever, "_ensure_fts_vocab_cache", lambda db: True)
    monkeypatch.setattr(retriever, "_suggest_term_correction", lambda **kwargs: None)
    monkeypatch.setattr(retriever, "_fetch_postings_for_near", lambda **kwargs: [])

    postings_by_term = {
        "neutropenia": [11],
        "febril": [11],
        "oncologica": [11],
    }

    monkeypatch.setattr(
        retriever,
        "_fetch_postings_for_term",
        lambda db, term, **kwargs: postings_by_term.get(str(term).lower(), []),
    )

    class _FakeQuery:
        def __init__(self, rows):
            self._rows = rows

        def filter(self, *args, **kwargs):
            return self

        def filter_by(self, **kwargs):
            specialty = kwargs.get("specialty")
            if specialty is None:
                return self
            filtered = [
                row
                for row in self._rows
                if getattr(row, "specialty", None) == specialty
            ]
            return _FakeQuery(filtered)

        def all(self):
            return list(self._rows)

    class _FakeDB:
        def __init__(self, rows):
            self._rows = rows

        def query(self, *args, **kwargs):
            return _FakeQuery(self._rows)

    db = _FakeDB([SimpleNamespace(id=11, specialty="oncology")])
    chunks, trace = retriever._fetch_candidate_chunks(
        query="Neutropenia febril oncologica pasos 0-10 y 10-60 con fuentes internas exactas.",
        db=db,
        specialty_filter=None,
        candidate_pool=64,
    )

    assert chunks
    assert trace["candidate_boolean_relaxed_union"] == "1"
    assert trace["candidate_strategy"] == "fts_boolean_relaxed_union"


def test_fetch_candidate_chunks_keeps_strict_no_match_for_explicit_boolean(monkeypatch):
    retriever = HybridRetriever()

    monkeypatch.setattr(retriever, "_ensure_sqlite_fts_index", lambda db: (True, {}))
    monkeypatch.setattr(retriever, "_ensure_fts_vocab_cache", lambda db: True)
    monkeypatch.setattr(retriever, "_suggest_term_correction", lambda **kwargs: None)
    monkeypatch.setattr(retriever, "_fetch_postings_for_near", lambda **kwargs: [])

    postings_by_term = {
        "neutropenia": [21],
        "febril": [21],
    }
    monkeypatch.setattr(
        retriever,
        "_fetch_postings_for_term",
        lambda db, term, **kwargs: postings_by_term.get(str(term).lower(), []),
    )

    class _FakeQuery:
        def filter(self, *args, **kwargs):
            return self

        def filter_by(self, **kwargs):
            return self

        def all(self):
            return []

    class _FakeDB:
        def query(self, *args, **kwargs):
            return _FakeQuery()

    chunks, trace = retriever._fetch_candidate_chunks(
        query="neutropenia AND febril AND sarampion",
        db=_FakeDB(),
        specialty_filter=None,
        candidate_pool=64,
    )

    assert chunks == []
    assert trace["candidate_boolean_relaxed_union"] == "0"
    assert trace["candidate_strategy"] == "fts_boolean_no_match"


def test_kgram_jaccard_similarity_is_higher_for_related_terms():
    left = HybridRetriever._build_kgrams("oncologia", 3)
    right = HybridRetriever._build_kgrams("oncologico", 3)
    far = HybridRetriever._build_kgrams("nefrologia", 3)
    assert HybridRetriever._jaccard_similarity(left, right) > HybridRetriever._jaccard_similarity(
        left, far
    )


def test_soundex_matches_reference_shape():
    assert HybridRetriever._soundex("Hermann") == "H655"
    assert HybridRetriever._soundex("Herman") == "H655"


def test_build_operand_context_map_tracks_neighbors():
    tokens = HybridRetriever._tokenize_boolean_query("flew form heathrow")
    context_map = HybridRetriever._build_operand_context_map(tokens)
    assert context_map["form"] == ("flew", "heathrow")


def test_context_term_from_neighbor_uses_phrase_edges():
    assert (
        HybridRetriever._context_term_from_neighbor('"shock septico"', use_last=True)
        == "septico"
    )
    assert (
        HybridRetriever._context_term_from_neighbor('"shock septico"', use_last=False)
        == "shock"
    )


def test_glob_to_regex_matches_expected_pattern():
    regex = HybridRetriever._glob_to_regex("oncol*")
    assert regex.match("oncologia")
    assert regex.match("oncologico")
    assert not regex.match("nefrologia")


def test_vb_gap_roundtrip_preserves_ids():
    ids = [3, 8, 12, 100, 103]
    payload = HybridRetriever._vb_encode_gaps(HybridRetriever._gaps_from_ids(ids))
    decoded_gaps = HybridRetriever._vb_decode_gaps(payload)
    decoded_ids = HybridRetriever._ids_from_gaps(decoded_gaps)
    assert decoded_ids == ids


def test_gamma_gap_roundtrip_preserves_ids():
    ids = [2, 5, 9, 15, 16, 120]
    payload = HybridRetriever._gamma_encode_gaps(HybridRetriever._gaps_from_ids(ids))
    decoded_gaps = HybridRetriever._gamma_decode_gaps(payload)
    decoded_ids = HybridRetriever._ids_from_gaps(decoded_gaps)
    assert decoded_ids == ids


def test_normalize_candidate_scores_scales_min_max():
    scored = [
        (SimpleNamespace(id=10), 2.0),
        (SimpleNamespace(id=11), 4.0),
        (SimpleNamespace(id=12), 6.0),
    ]
    normalized = HybridRetriever._normalize_candidate_scores(scored)
    assert normalized[10] == 0.0
    assert normalized[11] == 0.5
    assert normalized[12] == 1.0


def test_bm25_idf_increases_for_rarer_terms():
    common = HybridRetriever._bm25_idf(collection_size=100, doc_freq=80)
    rare = HybridRetriever._bm25_idf(collection_size=100, doc_freq=5)
    assert rare > common


def test_dirichlet_smoothed_prob_increases_with_doc_tf():
    low = HybridRetriever._dirichlet_smoothed_prob(
        doc_tf=0.0,
        doc_len=100.0,
        collection_prob=0.01,
        mu=1200.0,
    )
    high = HybridRetriever._dirichlet_smoothed_prob(
        doc_tf=8.0,
        doc_len=100.0,
        collection_prob=0.01,
        mu=1200.0,
    )
    assert high > low


def test_jm_smoothed_prob_uses_collection_backoff():
    pure_collection = HybridRetriever._jm_smoothed_prob(
        doc_tf=0.0,
        doc_len=80.0,
        collection_prob=0.02,
        lambda_value=0.0,
    )
    mixed = HybridRetriever._jm_smoothed_prob(
        doc_tf=4.0,
        doc_len=80.0,
        collection_prob=0.02,
        lambda_value=0.4,
    )
    assert abs(pure_collection - 0.02) < 1e-9
    assert mixed > pure_collection


def test_build_zone_weights_normalized_sum():
    retriever = HybridRetriever()
    weights = retriever._build_zone_weights()
    assert set(weights.keys()) == {
        "title",
        "section",
        "body",
        "keywords",
        "custom_questions",
    }
    assert abs(sum(weights.values()) - 1.0) < 1e-6


def test_keyword_tfidf_zone_scoring_prioritizes_title_hits():
    retriever = HybridRetriever()
    chunk_title_hit = DocumentChunk(
        id=101,
        document_id=101,
        chunk_text="manejo inicial y monitorizacion",
        chunk_index=0,
        section_path="protocolo",
        tokens_count=8,
        chunk_embedding=b"",
        keywords=[],
        custom_questions=[],
        specialty="oncology",
        content_type="paragraph",
    )
    chunk_title_hit.document = ClinicalDocument(
        id=101,
        title="Neutropenia febril oncologica",
        source_file="docs/76_motor_operativo_oncologia_urgencias.md",
        specialty="oncology",
        version=1,
        content_hash="a" * 64,
    )
    chunk_no_hit = DocumentChunk(
        id=102,
        document_id=102,
        chunk_text="manejo inicial y monitorizacion",
        chunk_index=0,
        section_path="protocolo",
        tokens_count=8,
        chunk_embedding=b"",
        keywords=[],
        custom_questions=[],
        specialty="oncology",
        content_type="paragraph",
    )
    chunk_no_hit.document = ClinicalDocument(
        id=102,
        title="Soporte general",
        source_file="docs/73_motor_operativo_nefrologia_urgencias.md",
        specialty="nephrology",
        version=1,
        content_hash="b" * 64,
    )

    scored, trace = retriever._score_keyword_candidates(
        query="neutropenia febril",
        chunks=[chunk_no_hit, chunk_title_hit],
        k=2,
    )
    assert scored
    assert scored[0][0].id == 101
    assert trace["keyword_search_method"].startswith("tfidf_zone_cosine_pivoted")
    assert trace["keyword_search_bm25_enabled"] == "1"
    assert trace["keyword_search_qlm_enabled"] == "1"


def test_keyword_scoring_empty_chunks_keeps_probabilistic_trace():
    retriever = HybridRetriever()
    scored, trace = retriever._score_keyword_candidates(
        query="neutropenia febril",
        chunks=[],
        k=3,
    )
    assert scored == []
    assert trace["keyword_search_chunks_found"] == "0"
    assert trace["keyword_search_bm25_enabled"] in {"0", "1"}
    assert "keyword_search_bm25_k1" in trace
    assert "keyword_search_bim_bonus_enabled" in trace
    assert "keyword_search_qlm_enabled" in trace
    assert "keyword_search_qlm_smoothing" in trace


def test_keyword_scoring_method_includes_qlm_when_enabled(monkeypatch):
    retriever = HybridRetriever()
    monkeypatch.setattr(settings, "CLINICAL_CHAT_RAG_BM25_ENABLED", False)
    monkeypatch.setattr(settings, "CLINICAL_CHAT_RAG_BIM_BINARY_BONUS_ENABLED", False)
    monkeypatch.setattr(settings, "CLINICAL_CHAT_RAG_QLM_ENABLED", True)
    monkeypatch.setattr(settings, "CLINICAL_CHAT_RAG_QLM_BLEND", 0.8)
    monkeypatch.setattr(settings, "CLINICAL_CHAT_RAG_QLM_SMOOTHING", "dirichlet")

    chunk = DocumentChunk(
        id=401,
        document_id=401,
        chunk_text="manejo de neutropenia febril con antibioterapia empirica",
        chunk_index=0,
        section_path="validacion",
        tokens_count=12,
        chunk_embedding=b"",
        keywords=["neutropenia", "fiebre"],
        custom_questions=[],
        specialty="oncology",
        content_type="paragraph",
    )
    chunk.document = ClinicalDocument(
        id=401,
        title="Motor Operativo de Oncologia",
        source_file="docs/76_motor_operativo_oncologia_urgencias.md",
        specialty="oncology",
        version=1,
        content_hash="f" * 64,
    )

    scored, trace = retriever._score_keyword_candidates(
        query="neutropenia febril",
        chunks=[chunk],
        k=1,
    )
    assert scored
    assert "+qlm" in trace["keyword_search_method"]
    assert "keyword_search_qlm_top_avg" in trace


def test_keyword_scoring_method_includes_lsi_when_enabled(monkeypatch):
    retriever = HybridRetriever()
    monkeypatch.setattr(settings, "CLINICAL_CHAT_RAG_BM25_ENABLED", False)
    monkeypatch.setattr(settings, "CLINICAL_CHAT_RAG_BIM_BINARY_BONUS_ENABLED", False)
    monkeypatch.setattr(settings, "CLINICAL_CHAT_RAG_QLM_ENABLED", False)
    monkeypatch.setattr(settings, "CLINICAL_CHAT_RAG_LSI_ENABLED", True)
    monkeypatch.setattr(settings, "CLINICAL_CHAT_RAG_LSI_BLEND", 0.8)
    monkeypatch.setattr(settings, "CLINICAL_CHAT_RAG_LSI_K", 4)
    monkeypatch.setattr(settings, "CLINICAL_CHAT_RAG_LSI_MIN_DOCS", 2)
    monkeypatch.setattr(settings, "CLINICAL_CHAT_RAG_LSI_MAX_VOCAB_TERMS", 128)

    chunk_onco = DocumentChunk(
        id=402,
        document_id=402,
        chunk_text="neutropenia febril con cultivos y antibiotico empirico",
        chunk_index=0,
        section_path="validacion",
        tokens_count=12,
        chunk_embedding=b"",
        keywords=["neutropenia", "fiebre"],
        custom_questions=[],
        specialty="oncology",
        content_type="paragraph",
    )
    chunk_onco.document = ClinicalDocument(
        id=402,
        title="Motor Operativo de Oncologia",
        source_file="docs/76_motor_operativo_oncologia_urgencias.md",
        specialty="oncology",
        version=1,
        content_hash="1" * 64,
    )
    chunk_hema = DocumentChunk(
        id=403,
        document_id=403,
        chunk_text="leucemia aguda con neutropenia y riesgo infeccioso",
        chunk_index=0,
        section_path="validacion",
        tokens_count=10,
        chunk_embedding=b"",
        keywords=["leucemia"],
        custom_questions=[],
        specialty="hematology",
        content_type="paragraph",
    )
    chunk_hema.document = ClinicalDocument(
        id=403,
        title="Motor Operativo de Hematologia",
        source_file="docs/71_motor_operativo_hematologia_urgencias.md",
        specialty="hematology",
        version=1,
        content_hash="2" * 64,
    )

    scored, trace = retriever._score_keyword_candidates(
        query="neutropenia febril",
        chunks=[chunk_onco, chunk_hema],
        k=2,
    )
    assert scored
    assert "+lsi" in trace["keyword_search_method"]
    assert "keyword_search_lsi_top_avg" in trace


def test_minimum_window_span_returns_smallest_window():
    tokens = ["neutropenia", "x", "fiebre", "y", "cultivos", "fiebre"]
    span = HybridRetriever._minimum_window_span(tokens, {"neutropenia", "fiebre"})
    assert span == 3


def test_estimate_static_quality_prefers_motor_operativo_document():
    high = DocumentChunk(
        id=201,
        document_id=201,
        chunk_text="texto",
        chunk_index=0,
        section_path="validacion",
        tokens_count=4,
        chunk_embedding=b"",
        keywords=[],
        custom_questions=[],
        specialty="oncology",
        content_type="paragraph",
    )
    high.document = ClinicalDocument(
        id=201,
        title="Motor Operativo de Oncologia",
        source_file="docs/76_motor_operativo_oncologia_urgencias.md",
        specialty="oncology",
        version=1,
        content_hash="c" * 64,
    )
    low = DocumentChunk(
        id=202,
        document_id=202,
        chunk_text="texto",
        chunk_index=0,
        section_path="notas",
        tokens_count=4,
        chunk_embedding=b"",
        keywords=[],
        custom_questions=[],
        specialty="",
        content_type="paragraph",
    )
    low.document = ClinicalDocument(
        id=202,
        title="Notas generales",
        source_file="tmp/misc.txt",
        specialty="",
        version=1,
        content_hash="d" * 64,
    )
    assert (
        HybridRetriever._estimate_static_quality(high)
        > HybridRetriever._estimate_static_quality(low)
    )


def test_expand_query_for_retrieval_details_uses_global_thesaurus_cache():
    HybridRetriever._global_thesaurus_cache_state = True
    HybridRetriever._global_thesaurus_cache_loaded_at = time.time()
    HybridRetriever._global_thesaurus_cache_terms = {
        "leucemia": ("neoplasia hematologica", "hemopatia maligna")
    }
    expanded_query, terms, _local, global_terms, _specialty = (
        HybridRetriever._expand_query_for_retrieval_details("Leucemia aguda")
    )
    assert "neoplasia hematologica" in expanded_query
    assert "neoplasia hematologica" in terms
    assert "neoplasia hematologica" in global_terms


def test_derive_prf_terms_extracts_candidates_from_seed_chunks():
    retriever = HybridRetriever()
    seed = DocumentChunk(
        id=301,
        document_id=301,
        chunk_text=(
            "Neutropenia febril con hemocultivos y antibioterapia empirica inmediata "
            "en paciente oncologico."
        ),
        chunk_index=0,
        section_path="validacion",
        tokens_count=22,
        chunk_embedding=b"",
        keywords=["hemocultivos", "antibioterapia"],
        custom_questions=[],
        specialty="oncology",
        content_type="paragraph",
    )
    terms = retriever._derive_prf_terms(
        query="neutropenia febril oncologica",
        seed_chunks=[seed],
    )
    assert any(term in {"hemocultivos", "antibioterapia", "empirica"} for term in terms)


def test_search_by_domain_filters_to_domain_specialties(db_session):
    retriever = HybridRetriever()

    doc_peds = ClinicalDocument(
        title="Pediatria",
        source_file="docs/86_motor_operativo_pediatria_neonatologia_urgencias.md",
        specialty="pediatrics_neonatology",
        version=1,
        content_hash="p" * 64,
    )
    doc_other = ClinicalDocument(
        title="SCASEST",
        source_file="docs/49_motor_scasest_urgencias.md",
        specialty="scasest",
        version=1,
        content_hash="s" * 64,
    )
    doc_null = ClinicalDocument(
        title="Sin especialidad",
        source_file="docs/misc.md",
        specialty=None,
        version=1,
        content_hash="n" * 64,
    )
    db_session.add_all([doc_peds, doc_other, doc_null])
    db_session.flush()

    db_session.add_all(
        [
            DocumentChunk(
                document_id=doc_peds.id,
                chunk_text="Pediatria neonatal: aislamiento y manejo inicial.",
                chunk_index=0,
                section_path="Pediatria",
                tokens_count=8,
                chunk_embedding=b"",
                keywords=["pediatria"],
                custom_questions=[],
                specialty="pediatrics_neonatology",
                content_type="paragraph",
            ),
            DocumentChunk(
                document_id=doc_other.id,
                chunk_text="Pediatria neonatal: texto de ruido cruzado.",
                chunk_index=0,
                section_path="SCASEST",
                tokens_count=8,
                chunk_embedding=b"",
                keywords=["pediatria"],
                custom_questions=[],
                specialty="scasest",
                content_type="paragraph",
            ),
            DocumentChunk(
                document_id=doc_null.id,
                chunk_text="Pediatria neonatal: texto sin especialidad.",
                chunk_index=0,
                section_path="General",
                tokens_count=8,
                chunk_embedding=b"",
                keywords=["pediatria"],
                custom_questions=[],
                specialty=None,
                content_type="paragraph",
            ),
        ]
    )
    db_session.commit()

    results, trace = retriever.search_by_domain(
        detected_domains=["pediatrics_neonatology"],
        db=db_session,
        query="sospecha pediatrica",
        k=5,
    )

    assert results
    assert all((item.specialty or "").lower() == "pediatrics_neonatology" for item in results)
    assert "pediatrics_neonatology" in trace["domain_search_specialties"]
    assert trace["domain_search_specialty_fallback"] == "0"


def test_search_by_domain_accepts_specialty_aliases(db_session):
    retriever = HybridRetriever()
    doc_alias = ClinicalDocument(
        title="Paliativos",
        source_file="docs/78_motor_operativo_cuidados_paliativos_urgencias.md",
        specialty="palliative_care",
        version=1,
        content_hash="a" * 64,
    )
    db_session.add(doc_alias)
    db_session.flush()
    db_session.add(
        DocumentChunk(
            document_id=doc_alias.id,
            chunk_text="Sedacion paliativa y control de dolor total.",
            chunk_index=0,
            section_path="Paliativos",
            tokens_count=9,
            chunk_embedding=b"",
            keywords=["paliativo"],
            custom_questions=[],
            specialty="palliative_care",
            content_type="paragraph",
        )
    )
    db_session.commit()

    results, trace = retriever.search_by_domain(
        detected_domains=["palliative"],
        db=db_session,
        query="dolor total en paliativos",
        k=3,
    )

    assert results
    assert results[0].specialty == "palliative_care"
    assert "palliative_care" in trace["domain_search_specialties"]
