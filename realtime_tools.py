import re

from logging_store import log_feedback, log_request
from query_classifier import classify_query_with_openai
from response_builder import (
    build_additional_troubleshooting_steps,
    build_no_steps_message,
    build_quick_summary,
    build_support_topic_title,
    build_ticket_help_items,
    extract_common_symptoms,
    extract_step_items,
    format_source_name,
)
from support_service import preferred_article_ids_for_category, resolve_question


SENSITIVE_PATTERNS = (
    (re.compile(r"(?i)(password\s*[:=]?\s*)(\S+)"), r"\1[redacted]"),
    (re.compile(r"(?i)(security answer\s*[:=]?\s*)(.+)"), r"\1[redacted]"),
    (re.compile(r"(?i)(mfa code\s*[:=]?\s*)(\d{4,8})"), r"\1[redacted]"),
    (re.compile(r"(?i)(verification code\s*[:=]?\s*)(\d{4,8})"), r"\1[redacted]"),
    (re.compile(r"(?i)(authenticator code\s*[:=]?\s*)(\d{4,8})"), r"\1[redacted]"),
)


def sanitize_ticket_text(value):
    """
    Remove obvious secrets from free-text fields before drafting a ticket.
    """
    if value is None:
        return None

    text = " ".join(str(value).strip().split())
    if not text:
        return None

    sanitized = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def _structured_support_payload(question, category=None):
    query_analysis = classify_query_with_openai(question)
    preferred_article_ids = preferred_article_ids_for_category(category)
    result = resolve_question(
        question,
        query_analysis=query_analysis,
        preferred_article_ids=preferred_article_ids,
    )

    full_document_text = result["full_document_text"]
    rendered_response = result["rendered_response"]
    source_name = result["source_name"]
    section_heading = result["section_heading"]

    support_title = build_support_topic_title(
        question=question,
        source_name=source_name,
        section_heading=section_heading,
        content_text=full_document_text,
    )
    steps = extract_step_items(
        rendered_response,
        content_text=full_document_text,
        question=question,
        section_heading=section_heading,
    )
    common_symptoms = extract_common_symptoms(
        rendered_response,
        content_text=full_document_text,
        question=question,
        section_heading=section_heading,
    )
    if_not_fixed = build_additional_troubleshooting_steps(
        question=question,
        source_name=source_name,
        content_text=full_document_text,
    )

    payload = {
        "matched_topic": support_title,
        "source": source_name,
        "source_title": format_source_name(source_name),
        "quick_summary": build_quick_summary(
            question=question,
            source_name=source_name,
            section_heading=section_heading,
            content_text=full_document_text,
            answer_text=rendered_response,
        ),
        "common_symptoms": common_symptoms,
        "steps": steps,
        "if_not_fixed": if_not_fixed,
        "escalation": result["escalation_text"],
        "confidence": result["retrieval_confidence"],
        "match_quality": result["retrieval_confidence"],
        "supported": result["supported"],
        "response_type": result["response_type"],
        "category_hint": category,
        "classified_intent": query_analysis.get("intent"),
        "classified_topic": query_analysis.get("topic"),
        "ticket_help_items": build_ticket_help_items(
            question=question,
            source_name=source_name,
            content_text=full_document_text,
        ),
        "password_reset_portal_url": result["password_reset_portal_url"],
    }

    if not steps:
        payload["no_steps_message"] = build_no_steps_message()

    return payload


def search_support_kb(query, category=None):
    """
    Reuse the retrieval-first support flow and return structured tool output.
    """
    if not query or not str(query).strip():
        raise ValueError("query is required")

    return _structured_support_payload(str(query).strip(), category=category)


def prepare_it_ticket(
    issue_summary,
    category,
    location=None,
    device=None,
    error_message=None,
    steps_tried=None,
    resolved=None,
):
    """
    Return a draft ticket payload without submitting anything externally.
    """
    clean_issue_summary = sanitize_ticket_text(issue_summary)
    clean_category = sanitize_ticket_text(category) or "general support"
    clean_location = sanitize_ticket_text(location)
    clean_device = sanitize_ticket_text(device)
    clean_error_message = sanitize_ticket_text(error_message)
    clean_steps_tried = sanitize_ticket_text(steps_tried)

    if not clean_issue_summary:
        raise ValueError("issue_summary is required")

    detail_fields = {
        "category": clean_category,
        "location": clean_location,
        "device": clean_device,
        "error_message": clean_error_message,
        "steps_tried": clean_steps_tried,
        "resolved": bool(resolved) if resolved is not None else None,
    }
    filtered_details = {key: value for key, value in detail_fields.items() if value not in (None, "")}

    draft_lines = [
        f"Issue summary: {clean_issue_summary}",
        f"Category: {clean_category}",
    ]
    if clean_location:
        draft_lines.append(f"Location: {clean_location}")
    if clean_device:
        draft_lines.append(f"Device/browser: {clean_device}")
    if clean_error_message:
        draft_lines.append(f"Error message: {clean_error_message}")
    if clean_steps_tried:
        draft_lines.append(f"Steps already tried: {clean_steps_tried}")
    if resolved is not None:
        draft_lines.append(f"Current status: {'Resolved' if resolved else 'Still needs help'}")

    return {
        "title": f"{clean_category.title()} support request",
        "issue_summary": clean_issue_summary,
        "details": filtered_details,
        "ticket_draft": "\n".join(draft_lines),
        "ready_to_submit": False,
        "safety_notes": [
            "Do not include passwords, full MFA codes, or security answers in the ticket.",
            "Use the exact error message and the steps already tried to help IT troubleshoot faster.",
        ],
    }


def log_support_interaction(user_question, category, resolved, escalated, notes=None):
    """
    Reuse the existing logging store for Realtime voice-agent interactions.
    """
    clean_question = sanitize_ticket_text(user_question)
    clean_category = sanitize_ticket_text(category) or "general"
    clean_notes = sanitize_ticket_text(notes)
    article_ids = preferred_article_ids_for_category(clean_category)
    article_id = article_ids[0] if article_ids else None

    if not clean_question:
        raise ValueError("user_question is required")

    request_log_id = log_request(
        question=clean_question,
        routed_topic=clean_category,
        article_id=article_id,
        supported=True,
        escalation_flag=bool(escalated),
        response_type="realtime_support_interaction",
        llm_used=False,
    )

    feedback_logged = False
    feedback_comment_parts = []
    if clean_notes:
        feedback_comment_parts.append(clean_notes)
    if escalated:
        feedback_comment_parts.append("Escalated to IT.")

    if resolved is not None or feedback_comment_parts:
        log_feedback(
            request_log_id=request_log_id,
            helpful=bool(resolved),
            comment=" ".join(feedback_comment_parts) or None,
        )
        feedback_logged = True

    return {
        "request_log_id": request_log_id,
        "feedback_logged": feedback_logged,
        "category": clean_category,
        "article_id": article_id,
        "resolved": bool(resolved),
        "escalated": bool(escalated),
    }


TOOL_HANDLERS = {
    "search_support_kb": search_support_kb,
    "prepare_it_ticket": prepare_it_ticket,
    "log_support_interaction": log_support_interaction,
}


REALTIME_FUNCTION_TOOLS = [
    {
        "type": "function",
        "name": "search_support_kb",
        "description": (
            "Search approved CCA IT support documentation and return structured troubleshooting guidance."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The user’s IT support question or problem statement.",
                },
                "category": {
                    "type": "string",
                    "description": (
                        "Optional category hint such as wifi, mfa, password, d2l, email, zoom, or classroom."
                    ),
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "prepare_it_ticket",
        "description": "Draft an IT support ticket summary without submitting it.",
        "parameters": {
            "type": "object",
            "properties": {
                "issue_summary": {
                    "type": "string",
                    "description": "Short summary of the unresolved issue.",
                },
                "category": {
                    "type": "string",
                    "description": "Support category such as wifi, mfa, password, d2l, email, zoom, or classroom.",
                },
                "location": {
                    "type": "string",
                    "description": "Optional location such as a classroom or campus area.",
                },
                "device": {
                    "type": "string",
                    "description": "Optional device, browser, or app information.",
                },
                "error_message": {
                    "type": "string",
                    "description": "Optional exact error message or visible warning text.",
                },
                "steps_tried": {
                    "type": "string",
                    "description": "Optional description of troubleshooting already attempted.",
                },
                "resolved": {
                    "type": "boolean",
                    "description": "Whether the issue is already resolved.",
                },
            },
            "required": ["issue_summary", "category"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "log_support_interaction",
        "description": "Log a support interaction outcome for analytics and follow-up tracking.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_question": {
                    "type": "string",
                    "description": "The user’s original support request.",
                },
                "category": {
                    "type": "string",
                    "description": "Support category associated with the interaction.",
                },
                "resolved": {
                    "type": "boolean",
                    "description": "Whether the issue was resolved during the interaction.",
                },
                "escalated": {
                    "type": "boolean",
                    "description": "Whether the issue needed escalation to IT.",
                },
                "notes": {
                    "type": "string",
                    "description": "Optional short notes about the outcome or handoff.",
                },
            },
            "required": ["user_question", "category", "resolved", "escalated"],
            "additionalProperties": False,
        },
    },
]


def dispatch_realtime_tool_call(tool_name, arguments):
    """
    Dispatch one Realtime function call to the local Python handler.
    """
    handler = TOOL_HANDLERS.get(tool_name)
    if handler is None:
        raise ValueError(f"Unknown tool: {tool_name}")

    return handler(**(arguments or {}))
