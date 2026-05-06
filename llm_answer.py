import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Try importing OpenAI
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# Defaults
DEFAULT_LLM_MODEL = "gpt-4.1-mini"
DEFAULT_TIMEOUT_SECONDS = 10.0


def llm_polishing_enabled():
    return os.environ.get("IT_SUPPORT_LLM_ENABLED", "0").strip() == "1"


def llm_model_name():
    return os.environ.get("IT_SUPPORT_LLM_MODEL", DEFAULT_LLM_MODEL).strip()


def openai_api_key():
    key = os.getenv("OPENAI_API_KEY")
    return key.strip() if key else None


def polish_answer(question, section_heading, article_id, answer_text):
    """
    Rewrite a retrieved answer into clearer student-facing language
    using only the supplied source text.

    Returns: (polished_text, llm_used)
    """

    if not answer_text or not answer_text.strip():
        return answer_text, False

    if not llm_polishing_enabled():
        return answer_text, False

    api_key = openai_api_key()

    if not api_key or OpenAI is None:
        return answer_text, False

    try:
        client = OpenAI(api_key=api_key, timeout=DEFAULT_TIMEOUT_SECONDS)

        instructions = (
            "You are polishing an IT support answer for Community College of Aurora students. "
            "Use only the provided question, article id, section heading, and source answer text. "
            "Do not use general knowledge. "
            "Do not invent URLs, policies, phone numbers, steps, account rules, or procedures not present in the source text. "
            "Keep the answer concise, clear, calm, and student-friendly. "
            "Do not mention that you are rewriting or summarizing. "
            "If the source text does not contain enough detail, say that the student should contact CCA IT Support."
        )

        source_payload = (
            f"Question:\n{question.strip()}\n\n"
            f"Article ID:\n{(article_id or '').strip()}\n\n"
            f"Section heading:\n{(section_heading or '').strip()}\n\n"
            f"Source answer text:\n{answer_text.strip()}\n"
        )

        response = client.responses.create(
            model=llm_model_name(),
            instructions=instructions,
            input=source_payload,
        )

        polished_text = (response.output_text or "").strip()

        if not polished_text:
            return answer_text, False

        return polished_text, True

    except Exception:
        # Fail safely
        return answer_text, False
