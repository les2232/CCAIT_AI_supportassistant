from agent_service import maybe_run_agent_triage
from llm_answer import polish_answer
from response_builder import extract_escalation_text, extract_first_url
from retriever import load_retrieval_texts, retrieve_best_section
from router import load_content_texts, select_response
from router import normalize_text


CATEGORY_ARTICLE_MAP = {
    "wifi": ["wifi-troubleshooting.txt"],
    "wireless": ["wifi-troubleshooting.txt"],
    "network": ["wifi-troubleshooting.txt"],
    "internet": ["wifi-troubleshooting.txt"],
    "mfa": ["mfa-account-security.txt"],
    "multi-factor authentication": ["mfa-account-security.txt"],
    "multifactor authentication": ["mfa-account-security.txt"],
    "authenticator": ["mfa-account-security.txt"],
    "password": ["password-reset.txt"],
    "account": ["password-reset.txt", "mfa-account-security.txt"],
    "d2l": ["d2l-troubleshooting.txt", "d2l.txt"],
    "brightspace": ["d2l-troubleshooting.txt", "d2l.txt"],
    "email": ["student-email-troubleshooting.txt", "student-email.txt"],
    "outlook": ["student-email-troubleshooting.txt", "student-email.txt"],
    "zoom": ["online-blended-learning.txt", "zoom-support.txt"],
    "classroom": ["classroom-technology.txt"],
    "projector": ["classroom-technology.txt"],
    "display": ["classroom-technology.txt"],
    "audio": ["classroom-technology.txt"],
}


def preferred_article_ids_for_category(category):
    """
    Return one or more preferred article ids for an optional category hint.
    """
    if not category:
        return None

    normalized = " ".join(str(category).strip().lower().split())
    if not normalized:
        return None

    if normalized.endswith(".txt"):
        return [normalized]

    article_ids = CATEGORY_ARTICLE_MAP.get(normalized)
    if article_ids:
        return article_ids

    return None


def adjust_query_analysis_for_retrieval(question, query_analysis):
    """
    Keep classifier output intact but remove misleading topic bias for MFA-style access failures.
    """
    if not isinstance(query_analysis, dict):
        return query_analysis

    normalized_question = normalize_text(question or "")
    if not normalized_question:
        return query_analysis

    verification_markers = (
        "verification code",
        "verification prompt",
        "not getting my verification code",
        "not receiving",
        "approve the mfa prompt",
        "cannot approve",
        "authenticator",
        "duo",
        "mfa",
    )
    email_markers = (
        "student email",
        "outlook",
        "email",
        "office 365",
        "microsoft 365",
    )

    if any(marker in normalized_question for marker in verification_markers) and not any(
        marker in normalized_question for marker in email_markers
    ):
        adjusted = dict(query_analysis)
        if adjusted.get("topic") == "email":
            adjusted["topic"] = "general"
        return adjusted

    return query_analysis


def resolve_question(question, query_analysis=None, preferred_article_ids=None):
    """
    Run the retrieval-first flow and return renderable response details.
    """
    source_name = None
    section_heading = None
    retrieval_confidence = None
    full_document_text = None
    rendered_response = None
    supported = False
    response_type = None
    escalation_text = None
    show_password_reset_portal = False
    password_reset_portal_url = None
    llm_used = False

    retrieval_query_analysis = adjust_query_analysis_for_retrieval(question, query_analysis)

    retrieval_texts = load_retrieval_texts()
    if preferred_article_ids:
        retrieval_texts = {
            article_id: text
            for article_id, text in retrieval_texts.items()
            if article_id in preferred_article_ids
        }

    retrieval_result = retrieve_best_section(
        question,
        content_texts=retrieval_texts,
        article_ids=preferred_article_ids,
        query_analysis=retrieval_query_analysis,
    )

    if retrieval_result is not None:
        source_name = retrieval_result.article_id
        section_heading = retrieval_result.section_heading
        retrieval_confidence = retrieval_result.confidence
        full_document_text = retrieval_result.full_document_text
        rendered_response = retrieval_result.answer_text
        supported = True
        response_type = "documentation_article"
        escalation_text = extract_escalation_text(full_document_text)

        if source_name == "password-reset.txt":
            show_password_reset_portal = True
            password_reset_portal_url = extract_first_url(full_document_text)
    else:
        routed_texts = load_content_texts()
        if preferred_article_ids:
            routed_texts = {
                article_id: text
                for article_id, text in routed_texts.items()
                if article_id in preferred_article_ids
            }

        source_name, raw_content = select_response(question, routed_texts)

        if source_name is None:
            response_type = "unsupported_topic"
            rendered_response = (
                "I don’t have official CCA IT documentation for that topic yet.\n"
                "For assistance with this issue, please contact the IT Help Desk."
            )
        elif not raw_content or not raw_content.strip():
            supported = True
            response_type = "documentation_unavailable"
            rendered_response = "The official documentation for this topic is currently unavailable."
        else:
            fallback_result = retrieve_best_section(
                question,
                content_texts={source_name: raw_content},
                article_ids=[source_name],
                min_score=1,
                query_analysis=retrieval_query_analysis,
            )
            supported = True
            response_type = "documentation_article"
            escalation_text = extract_escalation_text(raw_content)
            full_document_text = raw_content

            if fallback_result is not None:
                section_heading = fallback_result.section_heading
                retrieval_confidence = fallback_result.confidence
                rendered_response = fallback_result.answer_text
            else:
                rendered_response = raw_content.strip()

            if source_name == "password-reset.txt":
                show_password_reset_portal = True
                password_reset_portal_url = extract_first_url(raw_content)

    if response_type == "documentation_article" and rendered_response:
        rendered_response, llm_used = polish_answer(
            question=question,
            section_heading=section_heading,
            article_id=source_name,
            answer_text=rendered_response,
        )

    result = {
        "source_name": source_name,
        "section_heading": section_heading,
        "retrieval_confidence": retrieval_confidence,
        "full_document_text": full_document_text,
        "rendered_response": rendered_response,
        "supported": supported,
        "response_type": response_type,
        "escalation_text": escalation_text,
        "show_password_reset_portal": show_password_reset_portal,
        "password_reset_portal_url": password_reset_portal_url,
        "llm_used": llm_used,
    }
    return maybe_run_agent_triage(question, result)
