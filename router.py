from pathlib import Path
import re
from kb_scope import load_scoped_content_texts

CONTENT_DIR = Path(__file__).parent / "content"
EXCLUDED_DOCS = {
    "windows-11.txt",
    "cca-tech-help.txt",
}

TOPIC_CONFIGS = [
    {
        "article_id": "mfa-account-security.txt",
        "keywords": {
            "mfa": 7,
            "verification": 4,
            "authenticator": 5,
            "prompt": 4,
            "code": 3,
            "phone": 2,
            "lost": 3,
            "changed": 3,
        },
        "phrases": {
            "mfa": 8,
            "mfa keeps asking": 10,
            "mfa keeps prompting": 10,
            "lost my phone": 10,
            "lost phone": 9,
            "changed phones": 9,
            "changed phone": 9,
            "lost mfa access": 10,
            "multi factor": 8,
            "multi factor authentication": 9,
            "authenticator": 7,
            "verification code": 7,
        },
    },
    {
        "article_id": "password-reset.txt",
        "keywords": {
            "password": 4,
            "reset": 4,
            "login": 2,
            "signin": 2,
            "account": 2,
            "locked": 3,
            "mfa": 3,
            "verification": 2,
            "mycca": 3,
        },
        "phrases": {
            "password reset": 6,
            "reset my password": 6,
            "mycca": 5,
            "log in": 3,
            "sign in": 3,
            "cannot log in": 5,
            "can t log in": 5,
            "unable to log in": 5,
            "account locked": 6,
            "locked out": 6,
            "unlock my account": 6,
            "unlocking my account": 6,
            "mfa": 5,
            "multi factor": 5,
            "multi factor authentication": 6,
            "authenticator": 4,
            "verification code": 4,
        },
    },
    {
        "article_id": "wifi-troubleshooting.txt",
        "keywords": {
            "wifi": 5,
            "internet": 3,
            "network": 3,
            "wireless": 3,
            "connection": 2,
            "connect": 2,
            "students": 2,
            "showing": 2,
            "visible": 2,
            "see": 1,
        },
        "phrases": {
            "wi fi": 6,
            "wifi": 6,
            "cca students": 7,
            "wireless network": 5,
            "internet not working": 5,
            "cannot connect": 3,
            "can t connect": 3,
            "do not see cca students": 8,
            "student wifi is not showing": 8,
            "wifi is not showing": 7,
            "network issue": 4,
        },
    },
    {
        "article_id": "d2l.txt",
        "keywords": {
            "d2l": 5,
            "brightspace": 5,
            "class": 3,
            "course": 3,
            "assignment": 4,
            "assignments": 4,
            "homework": 4,
            "quiz": 3,
            "quizzes": 3,
            "materials": 2,
            "online": 2,
            "submit": 3,
        },
        "phrases": {
            "online class": 6,
            "online course": 6,
            "course materials": 5,
            "find my assignments": 6,
            "where do i find my assignments": 7,
            "submit assignments": 6,
            "submit homework": 6,
            "can t get into my online class": 7,
            "cannot get into my online class": 7,
            "learning management system": 6,
            "brightspace": 6,
        },
    },
    {
        "article_id": "student-laptops-calculators.txt",
        "keywords": {
            "laptop": 2,
            "calculator": 4,
            "loan": 3,
            "borrow": 4,
            "checkout": 3,
            "semester": 2,
            "graphing": 3,
            "ti84": 4,
        },
        "phrases": {
            "semester laptop": 6,
            "borrow a laptop": 6,
            "laptop loan": 6,
            "loaner laptop": 5,
            "borrow a calculator": 6,
            "graphing calculator": 6,
            "ti 84": 8,
            "check out a calculator": 6,
            "check out a laptop": 6,
        },
    },
    {
        "article_id": "student-email.txt",
        "keywords": {
            "email": 5,
            "outlook": 5,
            "office": 2,
            "mail": 3,
            "inbox": 3,
        },
        "phrases": {
            "student email": 7,
            "school email": 6,
            "email address": 4,
            "office 365": 6,
            "log into my student email": 7,
            "access my student email": 7,
        },
    },
    {
        "article_id": "online-blended-learning.txt",
        "keywords": {
            "zoom": 6,
            "online": 2,
            "blended": 2,
            "meeting": 2,
            "remote": 2,
        },
        "phrases": {
            "help with zoom": 8,
            "zoom meeting": 7,
            "zoom link": 5,
            "need help with zoom": 8,
            "remote class": 7,
            "video help": 3,
        },
    },
    {
        "article_id": "zoom-support.txt",
        "keywords": {
            "zoom": 6,
            "sso": 8,
            "company": 4,
            "domain": 5,
            "license": 6,
            "cccs": 5,
            "edu": 4,
        },
        "phrases": {
            "zoom sso": 12,
            "zoom sso login": 14,
            "zoom asks for sso": 14,
            "zoom company domain": 14,
            "company domain": 10,
            "cccs edu": 12,
            "zoom license": 12,
            "license not showing": 12,
        },
    },
    {
        "article_id": "printing.txt",
        "keywords": {
            "print": 5,
            "printer": 6,
            "printing": 5,
            "map": 7,
            "add": 3,
            "device": 2,
            "shared": 5,
            "path": 5,
            "error": 4,
            "showing": 3,
        },
        "phrases": {
            "map a printer": 12,
            "add a printer": 10,
            "shared printer": 10,
            "printer path": 9,
            "printer not showing": 10,
            "printer says error": 10,
            "printing problem": 8,
        },
    },
]

TOKEN_SYNONYMS = {
    "wi-fi": ("wifi",),
    "wireless": ("wifi",),
    "internet": ("wifi",),
    "network": ("wifi",),
    "signin": ("login",),
    "sign": ("login",),
    "logged": ("login",),
    "logging": ("login",),
    "locked": ("locked", "account"),
    "lockout": ("locked", "account"),
    "unlock": ("locked", "account"),
    "unlocking": ("locked", "account"),
    "mfa": ("mfa", "password", "account"),
    "multifactor": ("mfa",),
    "authenticator": ("mfa",),
    "verification": ("mfa",),
    "brightspace": ("d2l",),
    "mycourses": ("d2l",),
    "assignments": ("assignment",),
    "homework": ("assignment",),
    "class": ("course",),
    "courses": ("course",),
    "quizzes": ("quiz",),
    "outlook": ("email",),
    "office365": ("email",),
    "mail": ("email",),
    "laptops": ("laptop",),
    "calculators": ("calculator",),
    "borrowing": ("borrow",),
    "loaner": ("loan", "laptop"),
    "zoom": ("zoom", "online"),
    "printers": ("printer",),
    "printing": ("print", "printer"),
    "mapped": ("map", "printer"),
    "mapping": ("map", "printer"),
}


def load_content_texts(include_internal=False, internal_only=False):
    """
    Load scoped KB text files for fallback routing.
    Returns a dict: {article_id: text}.
    """
    texts = load_scoped_content_texts(
        include_internal=include_internal,
        internal_only=internal_only,
        content_dir=CONTENT_DIR,
    )
    for article_id in list(texts):
        if article_id in EXCLUDED_DOCS:
            texts.pop(article_id)
    return texts


def normalize_text(text):
    """Normalize text for routing comparisons."""
    text = text.lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    text = text.replace("-", " ")
    return re.sub(r"\s+", " ", text).strip()


def tokenize_text(text):
    """Tokenize normalized text into lowercase terms."""
    return re.findall(r"[a-z0-9]+", normalize_text(text))


def expand_query_tokens(question):
    """Return query tokens plus lightweight synonym expansions."""
    expanded = []
    for token in tokenize_text(question):
        expanded.append(token)
        expanded.extend(TOKEN_SYNONYMS.get(token, ()))
    return expanded


def score_topic(question, config):
    """Score one topic config against a user question."""
    normalized_question = normalize_text(question)
    expanded_tokens = expand_query_tokens(question)
    score = 0

    for phrase, weight in config["phrases"].items():
        if phrase in normalized_question:
            score += weight

    for token in expanded_tokens:
        score += config["keywords"].get(token, 0)

    return score


def legacy_select_response(question, content_texts):
    """Original hardcoded routing retained for comparison/evaluation."""
    q = question.strip().lower()

    if not q:
        return None, None

    if any(word in q for word in ["password", "login", "log in", "mycca"]):
        return "password-reset.txt", content_texts.get("password-reset.txt")

    if any(word in q for word in ["wifi", "internet", "network"]):
        return "wifi-troubleshooting.txt", content_texts.get("wifi-troubleshooting.txt")

    if any(
        phrase in q for phrase in [
            "d2l",
            "brightspace",
            "learning management system",
            "online course",
            "online class",
            "course material",
            "course materials",
            "submit assignment",
            "submit an assignment",
        ]
    ):
        return "d2l.txt", content_texts.get("d2l.txt")

    if any(
        phrase in q for phrase in [
            "semester laptop",
            "borrow a laptop",
            "borrow laptop",
            "check out a laptop",
            "checkout a laptop",
            "laptop loan",
            "loaner laptop",
            "borrow a calculator",
            "borrow calculator",
            "check out a calculator",
            "checkout a calculator",
            "graphing calculator",
            "ti-84",
        ]
    ):
        return "student-laptops-calculators.txt", content_texts.get("student-laptops-calculators.txt")

    if any(word in q for word in ["email", "outlook", "office", "student email"]):
        return "student-email.txt", content_texts.get("student-email.txt")

    return None, None


def select_response(question, content_texts, min_score=4):
    """
    Route a question to the best supported article using lightweight scoring.
    """
    if not question or not question.strip():
        return None, None
    normalized_question = normalize_text(question)
    if "duo" in normalized_question or normalized_question in {
        "verification code is not working",
        "the verification code is not working",
    }:
        return None, None

    best_config = None
    best_score = 0

    for config in TOPIC_CONFIGS:
        article_id = config["article_id"]
        if article_id not in content_texts:
            continue

        score = score_topic(question, config)
        if score > best_score:
            best_config = config
            best_score = score

    if not best_config or best_score < min_score:
        return None, None

    article_id = best_config["article_id"]
    return article_id, content_texts.get(article_id)
