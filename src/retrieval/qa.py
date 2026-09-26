from __future__ import annotations

from dataclasses import dataclass

from core.config import Settings
from core.utils import first_sentence
from retrieval.index import LocalEmbeddingIndex, SearchResult


@dataclass(frozen=True)
class AnswerResult:
    question: str
    answer: str
    retrieved_doc_ids: list[str]
    retrieved_contexts: list[str]
    retrieved_titles: list[str]


def _extract_answer(question: str, top_result: SearchResult) -> str:
    lowered = question.lower()
    metadata = top_result.metadata
    if "author" in lowered:
        return metadata["authors_joined"]
    if any(term in lowered for term in ("when was", "publication date", "published on", "published")):
        return metadata["published"]
    if "categor" in lowered:
        return metadata["categories_joined"]
    return first_sentence(metadata["summary"])


def answer_question(question: str, settings: Settings, index: LocalEmbeddingIndex, top_k: int | None = None) -> AnswerResult:
    # Evaluation must use vector retrieval only. Looking up a quoted title would
    # reveal the ground-truth document embedded in generated benchmark questions
    # and make retrieval_hit_rate artificially perfect.
    retrieved = index.search(question, top_k=top_k)
    if not retrieved:
        answer = "I don't know from the indexed corpus."
    else:
        answer = _extract_answer(question, retrieved[0])
    return AnswerResult(
        question=question,
        answer=answer,
        retrieved_doc_ids=[item.paper_id for item in retrieved],
        retrieved_contexts=[item.content for item in retrieved],
        retrieved_titles=[item.title for item in retrieved],
    )
