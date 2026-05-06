import json
import os

from llm_answer import OpenAI, openai_api_key
from retriever import classify_query_intent
from router import normalize_text


DEFAULT_CLASSIFIER_MODEL = "gpt-4.1-mini"
DEFAULT_CLASSIFIER_TIMEOUT_SECONDS = 6.0
ALLOWED_INTENTS = {"troubleshooting", "access", "contact", "informational"}
ALLOWED_TOPICS = {"wifi", "email", "d2l", "zoom", "classroom", "general"}


def classifier_model_name():
    return (
        os.environ.get("IT_SUPPORT_CLASSIFIER_MODEL", DEFAULT_CLASSIFIER_MODEL).strip()
        or DEFAULT_CLASSIFIER_MODEL
    )


def _local_topic_from_query(query):
    normalized = normalize_text(query)
    if any(
        term in normalized
        for term in (
            "wifi",
            "wi fi",
            "wireless",
            "internet",
            "network",
            "captive portal",
            "splash page",
            "sign in page",
        )
    ):
        return "wifi"
    if any(term in normalized for term in ("email", "outlook", "office 365", "microsoft 365")):
        return "email"
    if any(term in normalized for term in ("d2l", "brightspace", "course shell")):
        return "d2l"
    if "zoom" in normalized:
        return "zoom"
    if any(
        term in normalized
        for term in (
            "classroom",
            "projector",
            "display",
            "audio",
            "microphone",
            "av ",
            "touch panel",
            "instructor station",
        )
    ):
        return "classroom"
    return "general"


def classify_query_locally(query):
    """
    Deterministic fallback classification derived from the current heuristic logic.
    """
    normalized = normalize_text(query)
    topic = _local_topic_from_query(query)

    if (
        ("can t access" in normalized or "cannot access" in normalized)
        and ("class" in normalized or "course" in normalized)
    ):
        intent = "access"
        topic = "d2l"
    elif any(
        phrase in normalized
        for phrase in (
            "not working",
            "does not work",
            "doesn t work",
            "nothing is working",
            "broken",
            "error",
            "no internet",
            "no signal",
            "did not pop up",
            "never popped up",
            "not loading",
            "won t open",
            "won t load",
            "cannot connect",
            "can t connect",
            "cannot open",
            "can t open",
            "cannot sign in",
            "can t sign in",
            "cannot log in",
            "can t log in",
        )
    ):
        intent = "troubleshooting"
    elif any(
        phrase in normalized
        for phrase in (
            "who do i contact",
            "who can help",
            "where do i get help",
            "where can i get help",
            "where is",
            "office",
            "location",
            "located",
            "phone",
            "hours",
        )
    ):
        intent = "contact"
    elif any(
        phrase in normalized
        for phrase in (
            "how do i access",
            "how do i find",
            "how do i connect",
            "how do i join",
            "how do i submit",
            "how do i get started",
            "do i need",
            "where do i submit",
            "check out",
            "checkout",
            "borrow",
            "get started",
        )
    ):
        intent = "access"
    elif any(
        phrase in normalized
        for phrase in (
            "what is",
            "what does",
            "what are",
            "used for",
        )
    ):
        intent = "informational"
    else:
        local_intent = classify_query_intent(query)
        intent_map = {
            "troubleshooting": "troubleshooting",
            "access/setup": "access",
            "contact/help-location": "contact",
            "informational": "informational",
        }
        intent = intent_map.get(local_intent, "informational")

    if intent == "access" and topic == "general":
        if "class" in normalized or "course" in normalized:
            topic = "d2l"

    if intent == "contact" and "obl" in normalized:
        topic = "general"

    if intent == "troubleshooting" and "nothing is working" in normalized:
        topic = "general"

    confidence = {
        "troubleshooting": 0.82,
        "access": 0.78,
        "contact": 0.86,
        "informational": 0.64,
    }.get(intent, 0.6)
    if topic == "general":
        confidence = min(confidence, 0.68 if intent != "informational" else 0.48)
    return {
        "intent": intent,
        "topic": topic,
        "confidence": confidence,
    }


def _normalize_classifier_payload(payload, fallback):
    if not isinstance(payload, dict):
        return fallback

    intent = str(payload.get("intent", "")).strip().lower()
    topic = str(payload.get("topic", "")).strip().lower()

    try:
        confidence = float(payload.get("confidence", fallback["confidence"]))
    except (TypeError, ValueError):
        confidence = fallback["confidence"]

    if intent not in ALLOWED_INTENTS:
        intent = fallback["intent"]
    if topic not in ALLOWED_TOPICS:
        topic = fallback["topic"]

    confidence = max(0.0, min(confidence, 1.0))
    return {
        "intent": intent,
        "topic": topic,
        "confidence": confidence,
    }


def classify_query_with_openai(query):
    """
    Classify a user query into a small intent/topic schema using OpenAI.
    Falls back to deterministic local logic on any error or missing configuration.
    """
    fallback = classify_query_locally(query)
    if not query or not query.strip():
        return fallback

    api_key = openai_api_key()
    if not api_key or OpenAI is None:
        return fallback

    client = OpenAI(api_key=api_key, timeout=DEFAULT_CLASSIFIER_TIMEOUT_SECONDS)
    instructions = (
        "Classify the user query for a college IT support assistant. "
        "Return JSON only with keys intent, topic, confidence. "
        "Do not answer the question. Do not include markdown, commentary, or extra keys.\n\n"
        "Intent definitions:\n"
        "- troubleshooting: the user has a problem, error, broken tool, or cannot connect, load, open, or sign in.\n"
        "- access: the user asks how to access, find, connect, join, submit, check out, or get started.\n"
        "- contact: the user asks who to contact, where to get help, location, office, phone, email, or hours.\n"
        "- informational: the user asks what something is or what a tool is used for.\n\n"
        "Topic definitions:\n"
        "- wifi: Wi-Fi, internet, network connection, captive portal, splash page.\n"
        "- email: student email, Outlook, Microsoft 365 email.\n"
        "- d2l: D2L, Brightspace, online course shell, assignments, course materials.\n"
        "- zoom: Zoom, online meeting, video meeting, microphone, speaker, camera.\n"
        "- classroom: classroom display, projector, audio, room technology.\n"
        "- general: unclear, multiple topics, support routing, or non-matching tools.\n\n"
        "Use general when unsure instead of guessing.\n"
        "Confidence guidance:\n"
        "- high confidence is 0.80 or higher for clear topic and intent.\n"
        "- medium confidence is 0.50 to 0.79 for likely but imperfect matches.\n"
        "- low confidence is below 0.50 for unclear or multi-topic queries.\n\n"
        "Examples:\n"
        '- "my wifi says connected but no internet" -> {"intent":"troubleshooting","topic":"wifi","confidence":0.9}\n'
        '- "the wifi page never popped up" -> {"intent":"troubleshooting","topic":"wifi","confidence":0.88}\n'
        '- "student email not working" -> {"intent":"troubleshooting","topic":"email","confidence":0.91}\n'
        '- "student email verification is not working" -> {"intent":"troubleshooting","topic":"email","confidence":0.82}\n'
        '- "I can\'t access my class" -> {"intent":"access","topic":"d2l","confidence":0.58}\n'
        '- "Zoom audio is broken" -> {"intent":"troubleshooting","topic":"zoom","confidence":0.93}\n'
        '- "projector has no signal" -> {"intent":"troubleshooting","topic":"classroom","confidence":0.94}\n'
        '- "who do I contact for Zoom help" -> {"intent":"contact","topic":"zoom","confidence":0.94}\n'
        '- "where is OBL located" -> {"intent":"contact","topic":"general","confidence":0.72}\n'
        '- "what is D2L" -> {"intent":"informational","topic":"d2l","confidence":0.95}\n'
        '- "nothing is working" -> {"intent":"troubleshooting","topic":"general","confidence":0.35}\n'
    )
    prompt = (
        "User query:\n"
        f"{query.strip()}\n\n"
        "Return only JSON in this form:\n"
        '{"intent":"troubleshooting","topic":"wifi","confidence":0.91}'
    )

    try:
        response = client.responses.create(
            model=classifier_model_name(),
            instructions=instructions,
            input=prompt,
        )
        raw_output = (response.output_text or "").strip()
        if not raw_output:
            return fallback
        parsed = json.loads(raw_output)
        return _normalize_classifier_payload(parsed, fallback)
    except Exception:
        return fallback
