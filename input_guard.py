from dataclasses import dataclass, field
from typing import Optional

from router import normalize_text


DEFAULT_TOPIC_CHIPS = [
    {"label": "Wi-Fi help", "query": "Wi-Fi help"},
    {"label": "Password reset", "query": "Reset my password"},
    {"label": "MFA help", "query": "MFA help"},
    {"label": "D2L help", "query": "D2L help"},
    {"label": "Student email", "query": "Student email help"},
    {"label": "Printing", "query": "Printing help"},
    {"label": "Contact IT", "query": "Contact IT"},
]


@dataclass(frozen=True)
class InputGuardResult:
    kind: str
    title: str
    summary: str
    chips: list[dict[str, str]] = field(default_factory=list)
    should_retrieve: bool = False
    route_to_contact: bool = False


def _chip(label, query):
    return {"label": label, "query": query}


def classify_input_guard(user_input) -> Optional[InputGuardResult]:
    """
    Classify low-information inputs before retrieval.

    This guard is deterministic and intentionally small. It catches inputs that
    should not be forced into KB retrieval, while letting clear support
    questions continue through the normal retrieval-first flow.
    """
    normalized = normalize_text(user_input or "")
    if not normalized:
        return InputGuardResult(
            kind="vague_help",
            title="What do you need help with?",
            summary="Choose a topic below or type the system you are trying to use.",
            chips=DEFAULT_TOPIC_CHIPS,
        )

    greetings = {
        "hi",
        "hello",
        "hey",
        "hi there",
        "hello there",
        "hi how are you",
        "how are you",
    }
    closings = {
        "thanks",
        "thank you",
        "thank you so much",
        "ok",
        "okay",
    }
    vague_help = {
        "help",
        "i need help",
        "can you help me",
        "i need assistance",
        "can you assist me",
    }

    if normalized in greetings:
        return InputGuardResult(
            kind="greeting",
            title="How can I help with CCA technology?",
            summary="Choose a topic below, or type the technology issue you need help with.",
            chips=DEFAULT_TOPIC_CHIPS,
        )

    if normalized in closings:
        return InputGuardResult(
            kind="acknowledgment",
            title="You're welcome.",
            summary="If you still need IT help, choose a topic below or type the issue.",
            chips=DEFAULT_TOPIC_CHIPS,
        )

    if normalized in vague_help:
        return InputGuardResult(
            kind="vague_help",
            title="What do you need help with?",
            summary="Choose the closest topic so I can show the right approved support steps.",
            chips=DEFAULT_TOPIC_CHIPS,
        )

    if normalized == "computer":
        return InputGuardResult(
            kind="computer_clarification",
            title="What kind of computer help do you need?",
            summary="Choose the closest option so I can find the right support steps.",
            chips=[
                _chip("Login help", "I can't log in"),
                _chip("Lab computer", "Campus computer login help"),
                _chip("Laptop loan", "I need a laptop"),
                _chip("Classroom computer", "Classroom computer not working"),
                _chip("Software", "Software availability help"),
            ],
        )

    broad_login_phrases = {
        "i can t log in",
        "i cannot log in",
        "i cant log in",
        "i can t login",
        "i cannot login",
        "i cant login",
    }
    if normalized in broad_login_phrases:
        return InputGuardResult(
            kind="login_disambiguation",
            title="Which sign-in is not working?",
            summary="Choose the system you are trying to access.",
            chips=[
                _chip("D2L", "I cannot log into D2L"),
                _chip("Student email", "I cannot log into student email"),
                _chip("MyCCA", "My MyCCA account login is not working"),
                _chip("Campus computer", "I cannot log into a CCA computer"),
                _chip("Wi-Fi", "I cannot sign into Wi-Fi"),
                _chip("MFA/Auth", "MFA is not working"),
                _chip("I'm not sure", "Contact IT"),
            ],
        )

    vague_access_phrases = {
        "it won t let me in",
        "it wont let me in",
        "it won t let me log in",
        "it won t let me login",
        "it wont let me log in",
        "it wont let me login",
        "can t get in",
        "cant get in",
    }
    if normalized in vague_access_phrases:
        return InputGuardResult(
            kind="access_disambiguation",
            title="Which access problem is this?",
            summary="Choose the system or sign-in step that is blocking you.",
            chips=[
                _chip("D2L", "I cannot log into D2L"),
                _chip("Student email", "I cannot log into student email"),
                _chip("MyCCA", "My MyCCA account login is not working"),
                _chip("Campus computer", "I cannot log into a CCA computer"),
                _chip("Wi-Fi", "I cannot sign into Wi-Fi"),
                _chip("MFA/Auth", "MFA is not working"),
                _chip("I'm not sure", "Contact IT"),
            ],
        )

    mfa_clarification_phrases = {
        "mfa is not working",
        "my mfa is not working",
        "mfa not working",
        "mfa keeps asking me",
        "verification code is not working",
        "the verification code is not working",
        "duo keeps asking me again",
        "duo keeps asking me",
        "duo keeps prompting me",
        "duo verification is not working",
        "duo not working",
    }
    if normalized in mfa_clarification_phrases or normalized.startswith("duo "):
        return InputGuardResult(
            kind="mfa_disambiguation",
            title="Which MFA system are you using?",
            summary=(
                "Students use Microsoft Authenticator for MFA. Faculty and staff use Duo. "
                "Choose the option that matches your account."
            ),
            chips=[
                _chip("Student Microsoft Authenticator", "Microsoft Authenticator is not working"),
                _chip("Faculty/Staff Duo", "Contact IT"),
                _chip("I'm not sure", "Contact IT"),
            ],
        )

    contact_phrases = {
        "contact it",
        "contact the helpdesk",
        "contact helpdesk",
        "helpdesk",
        "helpdesk phone",
        "helpdesk phone number",
        "help desk phone",
        "help desk phone number",
        "how do i get help",
        "it phone number",
        "it helpdesk phone",
        "it helpdesk phone number",
        "it help desk phone",
        "it help desk phone number",
        "submit a ticket",
        "talk to someone",
    }
    if normalized in contact_phrases:
        return InputGuardResult(
            kind="contact_route",
            title="Contact CCA IT Support",
            summary="I will show the approved CCA IT contact information.",
            should_retrieve=True,
            route_to_contact=True,
        )

    return None
