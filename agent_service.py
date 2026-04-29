import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError


DEFAULT_AGENT_MODEL = "gpt-4.1-mini"
DEFAULT_AGENT_TIMEOUT_SECONDS = 6.0

SENSITIVE_PATTERNS = (
    (re.compile(r"(?i)(password\s*[:=]?\s*)(\S+)"), r"\1[redacted]"),
    (re.compile(r"(?i)(security answer\s*[:=]?\s*)(.+)"), r"\1[redacted]"),
    (re.compile(r"(?i)(mfa code\s*[:=]?\s*)(\d{4,8})"), r"\1[redacted]"),
    (re.compile(r"(?i)(verification code\s*[:=]?\s*)(\d{4,8})"), r"\1[redacted]"),
    (re.compile(r"(?i)(authenticator code\s*[:=]?\s*)(\d{4,8})"), r"\1[redacted]"),
)

try:
    from agents import Agent, Runner, function_tool
except Exception:
    Agent = None
    Runner = None

    def function_tool(func=None, **_kwargs):
        if func is None:
            return lambda wrapped: wrapped
        return func


def agents_enabled():
    return os.environ.get("ENABLE_AGENTS", "0").strip().lower() in {"1", "true", "yes", "on"}


def openai_api_key_configured():
    return bool(os.environ.get("OPENAI_API_KEY", "").strip())


def agent_model_name():
    return os.environ.get("IT_SUPPORT_AGENT_MODEL", DEFAULT_AGENT_MODEL).strip() or DEFAULT_AGENT_MODEL


def agent_timeout_seconds():
    raw_value = os.environ.get("IT_SUPPORT_AGENT_TIMEOUT_SECONDS", "").strip()
    if not raw_value:
        return DEFAULT_AGENT_TIMEOUT_SECONDS
    try:
        return max(1.0, float(raw_value))
    except ValueError:
        return DEFAULT_AGENT_TIMEOUT_SECONDS


def agent_available():
    return Agent is not None and Runner is not None


def sanitize_text(value):
    if value is None:
        return ""
    text = " ".join(str(value).strip().split())
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def compact_resolved_context(resolved_result):
    """
    Return only deterministic KB-derived fields that the agent may inspect.
    """
    resolved_result = resolved_result or {}
    return {
        "source_name": resolved_result.get("source_name"),
        "section_heading": resolved_result.get("section_heading"),
        "retrieval_confidence": resolved_result.get("retrieval_confidence"),
        "rendered_response": sanitize_text(resolved_result.get("rendered_response")),
        "supported": bool(resolved_result.get("supported")),
        "response_type": resolved_result.get("response_type"),
        "escalation_text": sanitize_text(resolved_result.get("escalation_text")),
        "show_password_reset_portal": bool(resolved_result.get("show_password_reset_portal")),
        "password_reset_portal_url": resolved_result.get("password_reset_portal_url"),
    }


@function_tool
def create_escalation_summary(
    user_question: str,
    source_name: str | None = None,
    section_heading: str | None = None,
    retrieved_context: str | None = None,
    escalation_text: str | None = None,
) -> str:
    """
    Draft a concise escalation summary from already-retrieved KB context.
    """
    lines = [
        f"Issue: {sanitize_text(user_question)}",
    ]
    if source_name:
        lines.append(f"Matched KB article: {sanitize_text(source_name)}")
    if section_heading:
        lines.append(f"Matched section: {sanitize_text(section_heading)}")
    if retrieved_context:
        lines.append(f"Relevant KB guidance: {sanitize_text(retrieved_context)[:700]}")
    if escalation_text:
        lines.append(f"Escalation guidance from KB: {sanitize_text(escalation_text)}")
    return "\n".join(lines)


def build_agent():
    if not agent_available():
        return None

    instructions = (
        "You are the Campus IT Triage Agent for Community College of Aurora. "
        "You produce structured metadata only. Do not write the main support answer. "
        "The local retrieved KB context is authoritative. Do not invent policies, Wi-Fi names, URLs, "
        "phone numbers, contact information, login steps, password reset steps, or escalation procedures. "
        "If the retrieved context is insufficient, say what information is missing and recommend escalation. "
        "Do not ask for or repeat passwords, MFA codes, security answers, or secrets. "
        "Return JSON only with these keys: triage_note, suggested_missing_info, ticket_summary, confidence_note, escalation_required. "
        "suggested_missing_info must be an array of short strings. escalation_required must be boolean. "
        "Never contradict or suppress escalation guidance provided in the KB context."
    )
    return Agent(
        name="Campus IT Triage Agent",
        model=agent_model_name(),
        instructions=instructions,
        tools=[create_escalation_summary],
    )


def build_agent_input(question, resolved_context):
    payload = {
        "user_question": sanitize_text(question),
        "retrieved_kb_context": resolved_context,
        "task": (
            "Review the retrieved KB context and produce additive triage metadata. "
            "Do not replace the answer, steps, source, section, or escalation."
        ),
    }
    return json.dumps(payload, ensure_ascii=True)


def extract_final_output(run_result):
    if run_result is None:
        return ""
    output = getattr(run_result, "final_output", None)
    if output is None:
        return ""
    if isinstance(output, str):
        return output
    try:
        return json.dumps(output)
    except TypeError:
        return str(output)


def parse_agent_payload(raw_output):
    if not raw_output or not str(raw_output).strip():
        return None
    text = str(raw_output).strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def normalize_agent_metadata(payload, resolved_context):
    if not isinstance(payload, dict):
        return None

    suggested_missing_info = payload.get("suggested_missing_info", [])
    if not isinstance(suggested_missing_info, list):
        suggested_missing_info = []
    suggested_missing_info = [
        sanitize_text(item)
        for item in suggested_missing_info
        if sanitize_text(item)
    ][:5]

    escalation_text = resolved_context.get("escalation_text") or ""
    escalation_required = bool(escalation_text) or bool(payload.get("escalation_required"))

    return {
        "agent_triage": {
            "used": True,
            "model": agent_model_name(),
            "triage_note": sanitize_text(payload.get("triage_note")),
            "escalation_required": escalation_required,
            "source_locked": True,
        },
        "suggested_missing_info": suggested_missing_info,
        "ticket_summary": sanitize_text(payload.get("ticket_summary")),
        "confidence_note": sanitize_text(payload.get("confidence_note")),
    }


def run_agent_with_timeout(agent, agent_input, runner=None):
    active_runner = runner or Runner

    def invoke():
        if hasattr(active_runner, "run_sync"):
            return active_runner.run_sync(agent, agent_input)
        return active_runner.run(agent, agent_input)

    executor = ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(invoke)
        return future.result(timeout=agent_timeout_seconds())
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def maybe_run_agent_triage(question, resolved_result, runner=None, agent_factory=None):
    """
    Add optional agent metadata to a deterministic support result.
    Returns the original result unchanged whenever the optional path is unavailable.
    """
    if not agents_enabled():
        return resolved_result
    if not openai_api_key_configured():
        return resolved_result
    if not agent_available() and runner is None and agent_factory is None:
        return resolved_result
    if not isinstance(resolved_result, dict):
        return resolved_result
    if resolved_result.get("response_type") not in {"documentation_article", "unsupported_topic"}:
        return resolved_result

    try:
        resolved_context = compact_resolved_context(resolved_result)
        agent = agent_factory() if agent_factory is not None else build_agent()
        if agent is None:
            return resolved_result

        run_result = run_agent_with_timeout(
            agent,
            build_agent_input(question, resolved_context),
            runner=runner,
        )
        payload = parse_agent_payload(extract_final_output(run_result))
        metadata = normalize_agent_metadata(payload, resolved_context)
        if not metadata:
            return resolved_result

        enriched = dict(resolved_result)
        enriched.update(metadata)
        return enriched
    except (TimeoutError, Exception):
        return resolved_result
