from app.retrieval.followup import condense_question, content_terms, is_followup


def test_is_followup_detects_pronouns_and_short_questions():
    assert is_followup("What about its parameters?")
    assert is_followup("and dense retrieval?")
    assert is_followup("Why?")
    assert not is_followup("How does reciprocal rank fusion combine rankings?")


def test_content_terms_drop_question_words():
    assert content_terms("How does BM25 work?") == ["bm25"]


def test_condense_carries_previous_topic():
    q = condense_question("What about its parameters?", ["How does BM25 work?"])
    assert q == "What about its parameters? (bm25)"


def test_condense_leaves_standalone_questions():
    q = "What is maximal marginal relevance?"
    assert condense_question(q, ["How does BM25 work?"]) == q
    assert condense_question("its parameters?", []) == "its parameters?"
