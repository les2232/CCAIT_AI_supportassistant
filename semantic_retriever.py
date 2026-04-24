import json
from functools import lru_cache
from pathlib import Path


CACHE_DIR = Path(__file__).parent / ".semantic_cache"
CACHE_PATH = CACHE_DIR / "section_index.json"


def build_section_text(section):
    """
    Combine section fields into one semantic search text.
    """
    parts = [
        section.get("document_title", "").strip(),
        section.get("section_heading", "").strip(),
        section.get("body_text", "").strip(),
    ]
    return "\n\n".join(part for part in parts if part).strip()


def get_file_timestamps(content_dir, article_ids):
    """
    Capture source file mtimes for cache invalidation.
    """
    timestamps = {}
    for article_id in sorted(article_ids):
        path = content_dir / article_id
        if not path.exists():
            return None
        timestamps[article_id] = path.stat().st_mtime
    return timestamps


def semantic_confidence_from_similarity(similarity):
    if similarity >= 0.7:
        return "high"
    if similarity >= 0.55:
        return "medium"
    return "low"


def cosine_similarity(query_vector, matrix):
    import numpy as np

    if matrix.size == 0:
        return np.array([])

    query_norm = np.linalg.norm(query_vector)
    matrix_norms = np.linalg.norm(matrix, axis=1)
    safe_denominator = np.clip(query_norm * matrix_norms, a_min=1e-12, a_max=None)
    return np.dot(matrix, query_vector) / safe_denominator


@lru_cache(maxsize=2)
def load_sentence_transformer(model_name):
    """
    Load the embedding model lazily so the app can fall back cleanly.
    """
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def load_cached_index(model_name, file_timestamps):
    """
    Load a cached section index if the source files still match.
    """
    if not CACHE_PATH.exists():
        return None

    try:
        payload = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    if payload.get("model_name") != model_name:
        return None
    if payload.get("file_timestamps") != file_timestamps:
        return None

    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        return None

    return payload


def write_cached_index(model_name, file_timestamps, entries):
    """
    Persist the semantic section index to disk.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "model_name": model_name,
        "file_timestamps": file_timestamps,
        "entries": entries,
    }
    CACHE_PATH.write_text(json.dumps(payload), encoding="utf-8")


def build_cached_index(sections, model_name, file_timestamps):
    """
    Build section embeddings and cache them locally.
    """
    model = load_sentence_transformer(model_name)
    section_texts = [build_section_text(section) for section in sections]
    embeddings = model.encode(section_texts, convert_to_numpy=True, show_progress_bar=False)

    entries = []
    for section, section_text, embedding in zip(sections, section_texts, embeddings):
        entries.append(
            {
                "article_id": section["article_id"],
                "section_heading": section["section_heading"],
                "section_text": section_text,
                "embedding": embedding.tolist(),
            }
        )

    write_cached_index(model_name=model_name, file_timestamps=file_timestamps, entries=entries)
    return {
        "model_name": model_name,
        "file_timestamps": file_timestamps,
        "entries": entries,
    }


def get_or_build_index(sections, model_name, file_timestamps):
    """
    Return a cached semantic index, rebuilding when inputs change.
    """
    cached = load_cached_index(model_name=model_name, file_timestamps=file_timestamps)
    if cached is not None:
        return cached
    return build_cached_index(
        sections=sections,
        model_name=model_name,
        file_timestamps=file_timestamps,
    )


def retrieve_best_semantic_section(question, sections, *, content_dir, model_name, min_similarity):
    """
    Return the best semantic match when embeddings are available and confident.
    """
    import numpy as np

    if not question or not question.strip() or not sections:
        return None

    article_ids = {section["article_id"] for section in sections}
    file_timestamps = get_file_timestamps(content_dir=content_dir, article_ids=article_ids)
    if file_timestamps is None:
        return None

    index_payload = get_or_build_index(
        sections=sections,
        model_name=model_name,
        file_timestamps=file_timestamps,
    )

    entries = index_payload.get("entries", [])
    if not entries:
        return None

    embedding_matrix = np.array([entry["embedding"] for entry in entries], dtype=float)
    model = load_sentence_transformer(model_name)
    question_embedding = model.encode(question, convert_to_numpy=True, show_progress_bar=False)
    similarities = cosine_similarity(question_embedding, embedding_matrix)
    if similarities.size == 0:
        return None

    best_index = int(np.argmax(similarities))
    best_similarity = float(similarities[best_index])
    if best_similarity < min_similarity:
        return None

    best_entry = entries[best_index]
    best_section = sections[best_index]
    return {
        "article_id": best_entry["article_id"],
        "section_heading": best_entry["section_heading"],
        "answer_text": best_section["answer_text"],
        "full_document_text": best_section["full_document_text"],
        "score": best_similarity,
        "confidence": semantic_confidence_from_similarity(best_similarity),
    }
