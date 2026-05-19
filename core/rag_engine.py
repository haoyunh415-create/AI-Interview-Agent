import os
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from core.config import EMBEDDING_PATH, MODEL_PATH, DB_PATH, RETRIEVAL_FETCH, RETRIEVAL_SCORE_THRESHOLD
from core.llm import get_llm

_embedding = None
_db = None


def get_embedding():
    global _embedding
    if _embedding is None:
        _embedding = HuggingFaceEmbeddings(
            model_name=EMBEDDING_PATH,
            cache_folder=MODEL_PATH,
        )
    return _embedding


def get_db():
    global _db
    if _db is None:
        if not os.path.exists(DB_PATH) or not os.listdir(DB_PATH):
            raise FileNotFoundError("Knowledge base not initialized. Run: python -m core.ingest_knowledge")
        _db = Chroma(persist_directory=DB_PATH, embedding_function=get_embedding())
    return _db


import re


def _keyword_overlap_penalty(query, text):
    """Calculate keyword mismatch penalty. Lower = better match.
    Heavy bias toward English technical terms (RLHF, LoRA, RAG, etc)."""
    query_lower = query.lower()
    text_lower = text.lower()

    query_chars = [c for c in query if c.strip()]
    if not query_chars:
        return 0

    # Character-level coverage
    matched = sum(1 for c in query_chars if c in text_lower)
    coverage = matched / len(query_chars)

    # Bigram overlap
    query_bigrams = {query[i:i+2] for i in range(len(query) - 1)}
    text_bigrams = {text_lower[i:i+2] for i in range(len(text_lower) - 1)}
    bigram_overlap = len(query_bigrams & text_bigrams) / len(query_bigrams) if query_bigrams else 0

    # English technical term matching with term frequency bonus
    query_eng_words = re.findall(r'[a-zA-Z]+', query_lower)
    if query_eng_words:
        tf_scores = []
        for word in query_eng_words:
            count = len(re.findall(re.escape(word), text_lower, re.IGNORECASE))
            tf_bonus = min(count / 3.0, 1.0) if count > 0 else 0.0
            tf_scores.append(tf_bonus)
        term_score = sum(tf_scores) / len(tf_scores)
        # English-heavy: term frequency dominates
        keyword_score = 1.0 - (coverage * 0.15 + bigram_overlap * 0.15 + term_score * 0.7)
    else:
        # Chinese-only query: balanced weighting
        keyword_score = 1.0 - (coverage * 0.5 + bigram_overlap * 0.5)
    return keyword_score


def search_best(query, score_threshold=RETRIEVAL_SCORE_THRESHOLD):
    """Hybrid search: vector similarity + keyword matching. Returns single best result.

    hybrid score range: 0-250 (lower = better match)
    """
    results = get_db().similarity_search_with_score(query, k=RETRIEVAL_FETCH)

    rescored = []
    for doc, vec_score in results:
        kw_penalty = _keyword_overlap_penalty(query, doc.page_content)
        vec_norm = min(vec_score / 2.0, 1.0)  # normalize L2 to 0-1
        hybrid = (vec_norm * 0.5 + kw_penalty * 0.5) * 250
        rescored.append((doc, hybrid))

    rescored.sort(key=lambda x: x[1])

    for doc, hybrid in rescored:
        if hybrid <= score_threshold:
            return doc, hybrid

    if rescored:
        return rescored[0][0], rescored[0][1]
    return None


def retrieve(query, score_threshold=RETRIEVAL_SCORE_THRESHOLD):
    result = search_best(query, score_threshold)
    if result is None:
        return ""
    return result[0].page_content


def retrieve_with_metadata(query, score_threshold=RETRIEVAL_SCORE_THRESHOLD):
    result = search_best(query, score_threshold)
    if result is None:
        return None
    doc, score = result
    return {
        "content": doc.page_content,
        "source": doc.metadata.get("source", "unknown"),
        "score": round(score, 1),
    }


def rag_query(query, api_key=None):
    result = search_best(query)
    if result is None:
        return "No relevant content found in the knowledge base.", []
    doc, _score = result

    prompt = (
        "You are an AI knowledge assistant. Answer based on the reference material.\n\n"
        "Reference:\n"
        f"{doc.page_content}\n\n"
        f"Question: {query}\n\n"
        "Requirements:\n"
        "1. Answer based on the reference, do not fabricate\n"
        "2. Be concise and direct\n"
        "3. If the reference is insufficient, honestly state so\n\n"
        "Answer:\n"
    )

    response = get_llm(api_key).invoke(prompt).content
    source = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
    return response, [source]
