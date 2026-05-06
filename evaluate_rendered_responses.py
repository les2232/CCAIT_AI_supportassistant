#!/usr/bin/env python3
import re
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from flask import template_rendered

from app import app, csrf_token_for_session


QUERIES = [
    "Classroom display won’t turn on",
    "Projector has no signal",
    "Audio not working in classroom",
    "Student email not working",
    "Connect to Wi-Fi",
    "Zoom not working",
    "Zoom audio is broken",
    "I am not getting my verification code",
    "Can I use OneDrive with my school account?",
    "Where is OBL located?",
    "Who can help with online course design?",
    "how do i connect to the internet?",
    "how do i connect to wifi?",
    "what wifi do students use?",
    "wifi not working",
    "i am connected to wifi but websites do not load",
    "i do not see CCA-Students",
    "my wifi password does not work",
]

INPUT_GUARD_CASES = [
    ("hi", "input_guard_greeting", ["Wi-Fi help", "Password reset", "MFA help"]),
    ("hello", "input_guard_greeting", ["Wi-Fi help", "Password reset", "MFA help"]),
    ("hi how are you", "input_guard_greeting", ["Wi-Fi help", "Password reset", "MFA help"]),
    ("thanks", "input_guard_acknowledgment", ["Wi-Fi help", "Contact IT"]),
    ("thank you", "input_guard_acknowledgment", ["Wi-Fi help", "Contact IT"]),
    ("ok", "input_guard_acknowledgment", ["Wi-Fi help", "Contact IT"]),
    ("help", "input_guard_vague_help", ["Wi-Fi help", "Password reset", "Contact IT"]),
    ("I need help", "input_guard_vague_help", ["Wi-Fi help", "Password reset", "Contact IT"]),
    ("can you help me", "input_guard_vague_help", ["Wi-Fi help", "Password reset", "Contact IT"]),
    ("computer", "input_guard_computer_clarification", ["Login help", "Laptop loan", "Classroom computer"]),
    ("I can’t log in", "input_guard_login_disambiguation", ["D2L", "Student email", "MyCCA", "Wi-Fi"]),
    ("it won't let me in", "input_guard_access_disambiguation", ["D2L", "Student email", "MFA/Auth", "I'm not sure"]),
    ("it won’t let me in", "input_guard_access_disambiguation", ["D2L", "Student email", "MFA/Auth", "I'm not sure"]),
]

CONTACT_CASES = [
    "contact IT",
    "helpdesk",
    "helpdesk phone",
    "helpdesk phone number",
    "how do I get help",
    "IT phone number",
    "submit a ticket",
    "talk to someone",
]

WEAK_QUERY_CASES = [
    {
        "query": "D2L is not loading",
        "source": "d2l-troubleshooting.txt",
        "section_contains": "Browser or cache issues",
        "support_title": "D2L Browser or Cache Issues",
        "step_terms": ("browser", "cache", "open d2l"),
    },
    {
        "query": "my email does not work",
        "source": "student-email-troubleshooting.txt",
        "section_contains": "email",
        "support_title": "Student Email or Outlook Not Loading",
        "step_terms": ("outlook", "web"),
    },
    {
        "query": "I need a laptop",
        "source": "student-laptops-calculators.txt",
        "section_contains": "semester laptop",
        "support_title": "How to Get a Semester Laptop",
        "step_terms": ("student success", "student id", "course schedule"),
    },
]

MFA_CLARIFICATION_CASES = [
    "MFA is not working",
    "verification code is not working",
    "Duo keeps asking me again",
    "Duo not working",
]

MFA_AUTHENTICATOR_CASES = [
    {
        "query": "I lost my phone and can't do MFA",
        "section_contains": "Changed phones or lost MFA access",
        "primary_label": "MFA recovery steps",
        "step_terms": ("correct cca account", "mfa", "contact the cca it helpdesk"),
    },
    {
        "query": "Microsoft Authenticator is not working",
        "section_contains": "Common MFA problems",
        "step_terms": ("microsoft authenticator", "verification"),
    },
    {
        "query": "Authenticator app not working",
        "section_contains": "Common MFA problems",
        "step_terms": ("authenticator", "verification"),
    },
    {
        "query": "add alternate MFA method",
        "section_contains": "Adding an alternate MFA method",
        "step_terms": ("student microsoft 365", "verification method"),
    },
]

D2L_ACCESS_CASES = [
    "my teacher said to use d2l but idk where it is",
    "where do I find D2L",
    "how do I access D2L",
    "where is my online class",
]

ZOOM_SSO_CASES = [
    {
        "query": "Zoom SSO login",
        "forbidden_terms": ("cccs-edu", "duo", "24 hours"),
    },
    {
        "query": "Zoom asks for SSO",
        "forbidden_terms": ("cccs-edu", "duo", "24 hours"),
    },
    {
        "query": "what is the Zoom company domain",
        "forbidden_terms": ("cccs-edu", "duo", "24 hours"),
    },
    {
        "query": "Zoom license not showing",
        "forbidden_terms": ("cccs-edu", "duo", "24 hours", "license sync"),
    },
]

PRINTING_CASES = [
    {
        "query": "how do I map a printer",
        "section_contains": "Printing",
        "forbidden_terms": ("ccadprint01", "select a shared printer by name", "ticket notes to include"),
    },
    {
        "query": "how do I add a printer",
        "section_contains": "Printing",
        "forbidden_terms": ("ccadprint01", "select a shared printer by name", "ticket notes to include"),
    },
    {
        "query": "printer not showing",
        "section_contains": "Common issues",
        "step_terms": ("printer", "not showing"),
    },
    {
        "query": "the printer says error",
        "section_contains": "Printer error message",
        "step_terms": ("exact printer error message",),
        "forbidden_terms": ("ccadprint01", "select a shared printer by name", "ticket notes to include"),
    },
]

GENERIC_TITLES = {
    "What this helps with",
    "Summary",
    "Context",
    "When to use it",
    "When to contact IT",
    "What to include when contacting IT",
    "What to include when asking for help",
}

METADATA_PATTERNS = (
    "TITLE:",
    "AUDIENCE:",
    "TAGS:",
    "CONTEXT:",
    "STEPS:",
    "IF NOT FIXED:",
    "ESCALATE:",
)


@contextmanager
def captured_templates(flask_app):
    recorded = []

    def record(sender, template, context, **extra):
        recorded.append((template, context))

    template_rendered.connect(record, flask_app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, flask_app)


def with_csrf(client, data):
    payload = dict(data)
    with client.session_transaction() as sess:
        payload["csrf_token"] = csrf_token_for_session(sess)
    return payload


def contains_guidance(step_list):
    joined = " ".join(step_list).lower()
    keywords = ("display", "projector", "input", "source", "laptop", "computer", "power")
    return any(keyword in joined for keyword in keywords)


def contains_email_troubleshooting(step_list):
    joined = " ".join(step_list).lower()
    keywords = ("password", "sign in", "outlook", "web", "email", "open")
    return any(keyword in joined for keyword in keywords)


def contains_email_verification_guidance(step_list):
    joined = " ".join(step_list).lower()
    keywords = ("microsoft authenticator", "authenticator", "mfa", "verification", "enrollment", "enroll", "prompt")
    return any(keyword in joined for keyword in keywords)


def contains_email_primary_duo_step(step_list):
    joined = " ".join(step_list).lower()
    has_duo_or_mfa = any(keyword in joined for keyword in ("microsoft authenticator", "authenticator", "mfa"))
    has_approve_or_prompt = any(keyword in joined for keyword in ("approve", "prompt"))
    return has_duo_or_mfa and has_approve_or_prompt


def contains_email_web_access_guidance(step_list):
    joined = " ".join(step_list).lower()
    return "outlook on the web" in joined or "web version" in joined


def contains_email_onboarding(step_list):
    joined = " ".join(step_list).lower()
    onboarding_terms = ("mycca", "icon", "school email address", "@student.cccs.edu")
    return any(term in joined for term in onboarding_terms)


def contains_wifi_portal_guidance(step_list):
    joined = " ".join(step_list).lower()
    keywords = ("accept", "sign-in page", "splash page", "captive portal")
    return any(keyword in joined for keyword in keywords)


def contains_wifi_setup_guidance(step_list):
    joined = " ".join(step_list).lower()
    keywords = ("wi-fi settings", "cca-students", "consent page", "open a web browser")
    return all(keyword in joined for keyword in keywords)


def contains_wifi_connected_no_internet_guidance(step_list):
    joined = " ".join(step_list).lower()
    keywords = ("connected to cca-students", "web browser", "consent page")
    return all(keyword in joined for keyword in keywords)


def contains_wifi_not_visible_guidance(step_list):
    joined = " ".join(step_list).lower()
    keywords = ("wi-fi is turned on", "wi-fi list", "cca-students")
    return any(keyword in joined for keyword in keywords)


def contains_wifi_password_guidance(step_list):
    joined = " ".join(step_list).lower()
    return "cca-students" in joined and "password" in joined


def has_repeated_step_text(step_list):
    normalized = [step.strip().lower() for step in step_list if step.strip()]
    return len(normalized) != len(set(normalized))


def contains_zoom_troubleshooting(step_list):
    joined = " ".join(step_list).lower()
    keywords = ("join", "browser", "audio", "microphone", "rejoin", "restart", "meeting")
    return any(keyword in joined for keyword in keywords)


def contains_zoom_audio_permission_guidance(step_list):
    joined = " ".join(step_list).lower()
    keywords = ("microphone", "speaker", "audio", "permission", "permissions")
    return any(keyword in joined for keyword in keywords)


def contains_verification_code_guidance(step_list):
    joined = " ".join(step_list).lower()
    keywords = ("verification code", "new verification code", "approve", "prompt", "authenticator")
    return any(keyword in joined for keyword in keywords)


def contains_onedrive_guidance(step_list):
    joined = " ".join(step_list).lower()
    keywords = ("onedrive", "microsoft 365", "school account", "sign in")
    return any(keyword in joined for keyword in keywords)


def contains_location_guidance(step_list):
    joined = " ".join(step_list).lower()
    keywords = ("go to", "fine arts building", "room f103", "location")
    return any(keyword in joined for keyword in keywords)


def contains_obl_contact_guidance(step_list):
    joined = " ".join(step_list).lower()
    keywords = ("onlinelearning.cca@ccaurora.edu", "course design", "instructional support", "obl")
    return any(keyword in joined for keyword in keywords)


def is_escalation_only(step_list):
    joined = " ".join(step_list).lower()
    escalation_terms = ("contact cca it support", "who to contact", "helpdesk", "call", "phone:")
    return bool(step_list) and all(any(term in step.lower() for term in escalation_terms) for step in step_list)


def is_heading_only(step):
    stripped = step.strip()
    if not stripped:
        return True
    return stripped.endswith(":") and len(stripped.split()) <= 12


def extract_guided_step_numbers(rendered_html):
    match = re.search(
        r'<ol class="response-steps guided-steps">(.*?)</ol>',
        rendered_html,
        flags=re.DOTALL,
    )
    if not match:
        return []
    return [int(value) for value in re.findall(r'<li data-step="(\d+)">', match.group(1))]


def extract_step_number_sequences(rendered_html):
    blocks = re.findall(
        r'<ol class="response-steps[^"]*">(.*?)</ol>',
        rendered_html,
        flags=re.DOTALL,
    )
    return [
        [int(value) for value in re.findall(r'<li data-step="(\d+)">', block)]
        for block in blocks
    ]


def has_sequential_rendered_step_numbers(rendered_html):
    numbers = extract_guided_step_numbers(rendered_html)
    return bool(numbers) and numbers == list(range(1, len(numbers) + 1))


def has_all_sequential_rendered_step_numbers(rendered_html):
    sequences = extract_step_number_sequences(rendered_html)
    return bool(sequences) and all(
        sequence == list(range(1, len(sequence) + 1))
        for sequence in sequences
    )


def fake_agent_metadata_result():
    content_text = (Path(__file__).parent / "content" / "wifi-troubleshooting.txt").read_text(
        encoding="utf-8"
    )
    return {
        "source_name": "wifi-troubleshooting.txt",
        "section_heading": "Cannot connect to CCA Wi-Fi:",
        "retrieval_confidence": "high",
        "full_document_text": content_text,
        "rendered_response": (
            "Cannot connect to CCA Wi-Fi:\n"
            "- Make sure Wi-Fi is turned on for your device.\n"
            "- Reconnect to CCA-Students and open a browser."
        ),
        "supported": True,
        "response_type": "documentation_article",
        "escalation_text": "Contact the CCA IT Helpdesk if you cannot connect to CCA-Students.",
        "show_password_reset_portal": False,
        "password_reset_portal_url": None,
        "llm_used": False,
        "agent_triage": {
            "used": True,
            "model": "fake-agent-model",
            "triage_note": "Fake triage note for rendered metadata evaluation.",
            "escalation_required": True,
            "source_locked": True,
        },
        "suggested_missing_info": [
            "Device type",
            "Campus location",
        ],
        "ticket_summary": "Fake ticket summary from retrieved Wi-Fi context.",
        "confidence_note": "Fake confidence note grounded in the matched KB section.",
    }


def evaluate_agent_metadata_rendering(client, failures):
    with patch(
        "app.classify_query_with_openai",
        return_value={"intent": "troubleshooting", "topic": "wifi", "confidence": 0.95},
    ), patch("app.resolve_question", return_value=fake_agent_metadata_result()):
        with captured_templates(app) as templates:
            response = client.post(
                "/",
                data=with_csrf(client, {"question": "Agent metadata rendering smoke"}),
                follow_redirects=True,
            )

    body = response.get_data(as_text=True)
    if response.status_code != 200:
        failures.append(("agent metadata rendering", f"unexpected status code: {response.status_code}"))
        return
    if not templates:
        failures.append(("agent metadata rendering", "no template context captured"))
        return

    required_text = (
        "Internal triage notes",
        "Fake triage note for rendered metadata evaluation.",
        "Escalation required: Yes",
        "Device type",
        "Campus location",
        "Fake ticket summary from retrieved Wi-Fi context.",
        "Fake confidence note grounded in the matched KB section.",
    )
    for text in required_text:
        if text not in body:
            failures.append(("agent metadata rendering", f"missing rendered text: {text}"))
            return

    _, context = templates[-1]
    if context.get("source_name") != "wifi-troubleshooting.txt":
        failures.append(("agent metadata rendering", "source_name was not preserved"))
        return
    if context.get("section_heading") != "Cannot connect to CCA Wi-Fi:":
        failures.append(("agent metadata rendering", "section_heading was not preserved"))
        return
    print("[PASS] 'agent metadata rendering'")


def evaluate_input_guard_cases(client, failures):
    for query, expected_response_type, expected_chip_text in INPUT_GUARD_CASES:
        with captured_templates(app) as templates:
            response = client.post("/", data=with_csrf(client, {"question": query}), follow_redirects=True)

        body = response.get_data(as_text=True)
        if response.status_code != 200:
            failures.append((query, f"unexpected status code: {response.status_code}"))
            continue
        if not templates:
            failures.append((query, "no template context captured"))
            continue

        _, context = templates[-1]
        guard_response = context.get("input_guard_response")
        guard_kind = getattr(guard_response, "kind", None)
        if guard_response is None or f"input_guard_{guard_kind}" != expected_response_type:
            failures.append((query, f"wrong guard response type: {guard_response}"))
            continue
        if context.get("source_name") is not None:
            failures.append((query, f"guard response retrieved an article: {context.get('source_name')}"))
            continue
        if context.get("retrieval_confidence") is not None:
            failures.append((query, "guard response exposed retrieval confidence"))
            continue
        for expected_text in expected_chip_text:
            escaped_text = expected_text.replace("'", "&#39;")
            if expected_text not in body and escaped_text not in body:
                failures.append((query, f"missing guard chip text: {expected_text}"))
                break
        else:
            if query == "hi" and "How can I help with CCA technology?" not in body:
                failures.append((query, "missing polished greeting title"))
                continue
            if query == "thanks" and "You&#39;re welcome." not in body and "You're welcome." not in body:
                failures.append((query, "missing polished acknowledgment title"))
                continue
            print(f"[PASS] {query!r}")


def evaluate_contact_guard_cases(client, failures):
    for query in CONTACT_CASES:
        with captured_templates(app) as templates:
            response = client.post("/", data=with_csrf(client, {"question": query}), follow_redirects=True)

        body = response.get_data(as_text=True)
        if response.status_code != 200:
            failures.append((query, f"unexpected status code: {response.status_code}"))
            continue
        if not templates:
            failures.append((query, "no template context captured"))
            continue

        _, context = templates[-1]
        if context.get("source_name") != "contact-it.txt":
            failures.append((query, f"wrong contact article: {context.get('source_name')}"))
            continue
        if context.get("response_type") != "documentation_article":
            failures.append((query, f"wrong contact response type: {context.get('response_type')}"))
            continue
        if (context.get("response_profile") or {}).get("kind") != "contact":
            failures.append((query, f"wrong response profile: {context.get('response_profile')}"))
            continue
        if "Try this first" in body:
            failures.append((query, "contact response rendered troubleshooting primary label"))
            continue
        if "Did this solve your issue?" in body:
            failures.append((query, "contact response rendered troubleshooting feedback"))
            continue
        if "response-steps guided-steps" in body:
            failures.append((query, "contact response rendered contact details as numbered steps"))
            continue
        if "after trying these steps" in body:
            failures.append((query, "contact response rendered troubleshooting escalation language"))
            continue
        if "Match confidence:" in body:
            failures.append((query, "contact response exposed match confidence"))
            continue
        if "CCA IT Helpdesk" not in body or "HelpdeskTickets.CCA@ccaurora.edu" not in body:
            failures.append((query, "contact response missing canonical helpdesk details"))
            continue
        for expected in (
            "Use the contact options above for CCA technology support.",
            "Include what you need help with.",
            "Include the device, app, or system involved.",
        ):
            if expected not in body:
                failures.append((query, f"contact response missing profile help text: {expected}"))
                break
        else:
            print(f"[PASS] {query!r}")
            continue


def evaluate_known_weak_queries(client, failures):
    for case in WEAK_QUERY_CASES:
        query = case["query"]
        with captured_templates(app) as templates:
            response = client.post("/", data=with_csrf(client, {"question": query}), follow_redirects=True)

        if response.status_code != 200:
            failures.append((query, f"unexpected status code: {response.status_code}"))
            continue
        if not templates:
            failures.append((query, "no template context captured"))
            continue

        _, context = templates[-1]
        source_name = context.get("source_name")
        section_heading = context.get("section_heading") or ""
        support_title = context.get("support_title")
        response_profile = context.get("response_profile") or {}
        guided_steps = context.get("guided_steps") or []
        joined_steps = " ".join(guided_steps).lower()
        body = response.get_data(as_text=True)

        if source_name != case["source"]:
            failures.append((query, f"wrong article: {source_name}"))
            continue
        if case["section_contains"].lower() not in section_heading.lower():
            failures.append((query, f"wrong section: {section_heading}"))
            continue
        if support_title in GENERIC_TITLES:
            failures.append((query, f"generic support title: {support_title}"))
            continue
        if case.get("support_title") and support_title != case["support_title"]:
            failures.append((query, f"wrong polished support title: {support_title}"))
            continue
        if not guided_steps:
            failures.append((query, "missing guided steps"))
            continue
        for term in case["step_terms"]:
            if term not in joined_steps:
                failures.append((query, f"guided steps missing {term!r}: {guided_steps}"))
                break
        else:
            if query == "I need a laptop":
                if response_profile.get("kind") != "checkout":
                    failures.append((query, f"wrong response profile: {response_profile}"))
                    continue
                generic_fallback = (
                    "Confirm the exact system, room, device, or account involved",
                    "Retry the procedure from the beginning",
                    "Search again using the product name",
                )
                if any(text in body for text in generic_fallback):
                    failures.append((query, "checkout response rendered generic troubleshooting fallback"))
                    continue
                if "Try this first" in body:
                    failures.append((query, "checkout response rendered troubleshooting primary label"))
                    continue
                if "Did this solve your issue?" in body:
                    failures.append((query, "checkout response rendered troubleshooting feedback prompt"))
                    continue
                for expected in (
                    "Bring your student ID.",
                    "Bring or know your current course schedule.",
                    "Explain what device or checkout item you need.",
                ):
                    if expected not in body:
                        failures.append((query, f"checkout response missing profile help text: {expected}"))
                        break
                else:
                    if "Include the exact error message or screenshot." in body:
                        failures.append((query, "checkout response rendered generic error/screenshot guidance"))
                        continue
            if query in {"D2L is not loading", "my email does not work"}:
                if response_profile.get("kind") != "troubleshooting":
                    failures.append((query, f"troubleshooting query used wrong profile: {response_profile}"))
                    continue
                if body.count("student ID") > 1 or body.count("CCA username") > 1:
                    failures.append((query, "troubleshooting help box repeated account ID guidance"))
                    continue
            print(f"[PASS] {query!r}")


def evaluate_access_cleanup_cases(client, failures):
    for query in D2L_ACCESS_CASES:
        with captured_templates(app) as templates:
            response = client.post("/", data=with_csrf(client, {"question": query}), follow_redirects=True)

        body = response.get_data(as_text=True)
        if response.status_code != 200:
            failures.append((query, f"unexpected status code: {response.status_code}"))
            continue
        if not templates:
            failures.append((query, "no template context captured"))
            continue

        _, context = templates[-1]
        source_name = context.get("source_name")
        support_title = context.get("support_title")
        section_heading = context.get("section_heading") or ""
        guided_steps = context.get("guided_steps") or []
        joined_steps = " ".join(guided_steps).lower()

        if source_name not in {"d2l.txt", "d2l-troubleshooting.txt"}:
            failures.append((query, f"wrong D2L article: {source_name}"))
            continue
        if support_title in GENERIC_TITLES or support_title == "If that did not work":
            failures.append((query, f"bad D2L access title: {support_title}"))
            continue
        if "If that did not work" in body and support_title == "If that did not work":
            failures.append((query, "D2L fallback heading rendered as main title"))
            continue
        if "assignment upload" in section_heading.lower():
            failures.append((query, f"D2L access query selected assignment upload: {section_heading}"))
            continue
        if not guided_steps or not any(term in joined_steps for term in ("d2l", "brightspace", "course")):
            failures.append((query, f"D2L access steps missing course-access guidance: {guided_steps}"))
            continue
        print(f"[PASS] {query!r}")

    query = "I can't get into my homework"
    with captured_templates(app) as templates:
        response = client.post("/", data=with_csrf(client, {"question": query}), follow_redirects=True)

    if response.status_code != 200:
        failures.append((query, f"unexpected status code: {response.status_code}"))
    elif not templates:
        failures.append((query, "no template context captured"))
    else:
        _, context = templates[-1]
        source_name = context.get("source_name")
        section_heading = context.get("section_heading") or ""
        support_title = context.get("support_title")
        if source_name not in {"d2l.txt", "d2l-troubleshooting.txt"}:
            failures.append((query, f"homework access routed outside D2L: {source_name}"))
        elif "assignment upload" in section_heading.lower():
            failures.append((query, f"homework access incorrectly selected assignment upload: {section_heading}"))
        elif support_title in GENERIC_TITLES or support_title == "If that did not work":
            failures.append((query, f"bad homework access title: {support_title}"))
        else:
            print(f"[PASS] {query!r}")

    query = "I am new and need to get online"
    with captured_templates(app) as templates:
        response = client.post("/", data=with_csrf(client, {"question": query}), follow_redirects=True)

    body = response.get_data(as_text=True)
    if response.status_code != 200:
        failures.append((query, f"unexpected status code: {response.status_code}"))
    elif not templates:
        failures.append((query, "no template context captured"))
    else:
        _, context = templates[-1]
        if context.get("source_name") != "wifi-troubleshooting.txt":
            failures.append((query, f"wrong Wi-Fi article: {context.get('source_name')}"))
        elif context.get("support_title") != "Student Wi-Fi Setup":
            failures.append((query, f"wrong Wi-Fi setup title: {context.get('support_title')}"))
        elif not has_all_sequential_rendered_step_numbers(body):
            failures.append((query, f"step numbers not sequential: {extract_step_number_sequences(body)}"))
        elif not contains_wifi_setup_guidance(context.get("guided_steps") or []):
            failures.append((query, f"missing Wi-Fi setup guidance: {context.get('guided_steps')}"))
        else:
            print(f"[PASS] {query!r}")

    query = "internet broke"
    with captured_templates(app) as templates:
        response = client.post("/", data=with_csrf(client, {"question": query}), follow_redirects=True)

    if response.status_code != 200:
        failures.append((query, f"unexpected status code: {response.status_code}"))
    elif not templates:
        failures.append((query, "no template context captured"))
    else:
        _, context = templates[-1]
        additional_steps = context.get("additional_steps") or []
        if context.get("source_name") != "wifi-troubleshooting.txt":
            failures.append((query, f"wrong Wi-Fi article: {context.get('source_name')}"))
        elif context.get("support_title") != "Wi-Fi or Internet Not Working":
            failures.append((query, f"wrong Wi-Fi troubleshooting title: {context.get('support_title')}"))
        elif len(additional_steps) > 6:
            failures.append((query, f"too many Wi-Fi follow-up steps: {additional_steps}"))
        elif has_repeated_step_text(additional_steps):
            failures.append((query, f"duplicate Wi-Fi follow-up steps: {additional_steps}"))
        else:
            print(f"[PASS] {query!r}")


def evaluate_zoom_sso_cases(client, failures):
    for case in ZOOM_SSO_CASES:
        query = case["query"]
        with captured_templates(app) as templates:
            response = client.post("/", data=with_csrf(client, {"question": query}), follow_redirects=True)

        if response.status_code != 200:
            failures.append((query, f"unexpected status code: {response.status_code}"))
            continue
        if not templates:
            failures.append((query, "no template context captured"))
            continue

        _, context = templates[-1]
        source_name = context.get("source_name")
        guided_steps = context.get("guided_steps") or []
        joined_steps = " ".join(guided_steps).lower()
        body = response.get_data(as_text=True).lower()

        if source_name != "zoom-support.txt":
            failures.append((query, f"wrong Zoom SSO article: {source_name}"))
            continue
        for term in case.get("forbidden_terms", ()):
            if term.lower() in joined_steps or term.lower() in body:
                failures.append((query, f"public Zoom response leaked internal term {term!r}"))
                break
        else:
            for term in case.get("step_terms", ()):
                if term.lower() not in joined_steps and term.lower() not in body:
                    failures.append((query, f"Zoom SSO response missing {term!r}: {guided_steps}"))
                    break
            else:
                print(f"[PASS] {query!r}")
            continue
        continue


def evaluate_printing_cases(client, failures):
    for case in PRINTING_CASES:
        query = case["query"]
        with captured_templates(app) as templates:
            response = client.post("/", data=with_csrf(client, {"question": query}), follow_redirects=True)

        if response.status_code != 200:
            failures.append((query, f"unexpected status code: {response.status_code}"))
            continue
        if not templates:
            failures.append((query, "no template context captured"))
            continue

        _, context = templates[-1]
        source_name = context.get("source_name")
        section_heading = context.get("section_heading") or ""
        guided_steps = context.get("guided_steps") or []
        joined_steps = " ".join(guided_steps).lower()
        body = response.get_data(as_text=True).lower()

        if source_name != "printing.txt":
            failures.append((query, f"wrong printing article: {source_name}"))
            continue
        if case["section_contains"].lower() not in section_heading.lower():
            failures.append((query, f"wrong printing section: {section_heading}"))
            continue
        if context.get("input_guard_response") is not None:
            failures.append((query, "printing query was stopped by input guard instead of KB retrieval"))
            continue
        for term in case.get("forbidden_terms", ()):
            if term.lower() in joined_steps or term.lower() in body:
                failures.append((query, f"public printing response leaked internal term {term!r}"))
                break
        else:
            for term in case.get("step_terms", ()):
                if term.lower() not in joined_steps and term.lower() not in body:
                    failures.append((query, f"printing response missing {term!r}: {guided_steps}"))
                    break
            else:
                if query == "the printer says error" and "Printing from personal devices" in body:
                    failures.append((query, "printer error assumed personal-device printing"))
                    continue
                print(f"[PASS] {query!r}")
            continue
        continue


def evaluate_mfa_clarification_cases(client, failures):
    expected_labels = ("Student Microsoft Authenticator", "Faculty/Staff Duo", "I'm not sure")
    for query in MFA_CLARIFICATION_CASES:
        with captured_templates(app) as templates:
            response = client.post("/", data=with_csrf(client, {"question": query}), follow_redirects=True)

        body = response.get_data(as_text=True)
        if response.status_code != 200:
            failures.append((query, f"unexpected status code: {response.status_code}"))
            continue
        if not templates:
            failures.append((query, "no template context captured"))
            continue

        _, context = templates[-1]
        guard_response = context.get("input_guard_response")
        if getattr(guard_response, "kind", None) != "mfa_disambiguation":
            failures.append((query, f"wrong MFA clarification response: {guard_response}"))
            continue
        if context.get("source_name") is not None:
            failures.append((query, f"MFA clarification retrieved an article: {context.get('source_name')}"))
            continue
        for expected_label in expected_labels:
            escaped_label = expected_label.replace("'", "&#39;")
            if expected_label not in body and escaped_label not in body:
                failures.append((query, f"missing MFA clarification option: {expected_label}"))
                break
        else:
            print(f"[PASS] {query!r}")


def evaluate_mfa_authenticator_cases(client, failures):
    for case in MFA_AUTHENTICATOR_CASES:
        query = case["query"]
        with captured_templates(app) as templates:
            response = client.post("/", data=with_csrf(client, {"question": query}), follow_redirects=True)

        body = response.get_data(as_text=True)
        if response.status_code != 200:
            failures.append((query, f"unexpected status code: {response.status_code}"))
            continue
        if not templates:
            failures.append((query, "no template context captured"))
            continue

        _, context = templates[-1]
        source_name = context.get("source_name")
        section_heading = context.get("section_heading") or ""
        response_profile = context.get("response_profile") or {}
        guided_steps = context.get("guided_steps") or []
        joined_steps = " ".join(guided_steps).lower()

        if source_name != "mfa-account-security.txt":
            failures.append((query, f"wrong MFA article: {source_name}"))
            continue
        if case["section_contains"].lower() not in section_heading.lower():
            failures.append((query, f"wrong MFA section: {section_heading}"))
            continue
        if response_profile.get("kind") != "troubleshooting":
            failures.append((query, f"MFA query used wrong profile: {response_profile}"))
            continue
        if "Contact details" in body:
            failures.append((query, "MFA query rendered contact primary label"))
            continue
        if "Match confidence:" in body:
            failures.append((query, "MFA query exposed match confidence"))
            continue
        if len(guided_steps) > 6:
            failures.append((query, f"MFA steps too long/repetitive: {guided_steps}"))
            continue
        if case.get("primary_label") and case["primary_label"] not in body:
            failures.append((query, f"missing MFA primary label: {case['primary_label']}"))
            continue
        for term in case["step_terms"]:
            if term not in joined_steps:
                failures.append((query, f"MFA steps missing {term!r}: {guided_steps}"))
                break
        else:
            print(f"[PASS] {query!r}")


def main():
    failures = []

    print("Rendered response evaluation")
    print("=" * 72)

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["username"] = "testuser"

        evaluate_input_guard_cases(client, failures)
        evaluate_contact_guard_cases(client, failures)
        evaluate_known_weak_queries(client, failures)
        evaluate_access_cleanup_cases(client, failures)
        evaluate_zoom_sso_cases(client, failures)
        evaluate_printing_cases(client, failures)
        evaluate_mfa_clarification_cases(client, failures)
        evaluate_mfa_authenticator_cases(client, failures)

        for query in QUERIES:
            with captured_templates(app) as templates:
                response = client.post("/", data=with_csrf(client, {"question": query}), follow_redirects=True)

            if response.status_code != 200:
                failures.append((query, f"unexpected status code: {response.status_code}"))
                continue

            if not templates:
                failures.append((query, "no template context captured"))
                continue

            if "Internal triage notes" in response.get_data(as_text=True):
                failures.append((query, "agent metadata block rendered when metadata was absent"))
                continue

            body = response.get_data(as_text=True)
            if "Match confidence:" in body:
                failures.append((query, "student-facing response exposed match confidence"))
                continue

            _, context = templates[-1]
            source_name = context.get("source_name")
            section_heading = context.get("section_heading")
            support_title = context.get("support_title")
            guided_steps = context.get("guided_steps") or []
            escalation_text = context.get("escalation_text") or ""

            if support_title in GENERIC_TITLES:
                failures.append((query, f"generic support title: {support_title}"))
                continue

            if query == "Zoom not working":
                if source_name != "zoom-support.txt":
                    failures.append((query, f"wrong article: {source_name}"))
                    continue
                if section_heading in {"When to contact IT for Zoom help:", "Still need help with Zoom?"}:
                    failures.append((query, f"escalation section selected instead of troubleshooting: {section_heading}"))
                    continue
                if len(guided_steps) < 3:
                    failures.append((query, f"too few guided steps: {guided_steps}"))
                    continue
                if any(any(label in step for label in METADATA_PATTERNS) for step in guided_steps):
                    failures.append((query, f"metadata leaked into guided steps: {guided_steps}"))
                    continue
                if is_escalation_only(guided_steps):
                    failures.append((query, f"guided steps are escalation-only: {guided_steps}"))
                    continue
                if not contains_zoom_troubleshooting(guided_steps):
                    failures.append((query, f"guided steps missing Zoom troubleshooting guidance: {guided_steps}"))
                    continue
                print(f"[PASS] {query!r}")
                print(f"  article: {source_name}")
                print(f"  section: {section_heading}")
                print(f"  steps:   {guided_steps[:4]}")
                continue

            if query == "Zoom audio is broken":
                if source_name != "zoom-support.txt":
                    failures.append((query, f"wrong article: {source_name}"))
                    continue
                if len(guided_steps) < 3:
                    failures.append((query, f"too few guided steps: {guided_steps}"))
                    continue
                if any(any(label in step for label in METADATA_PATTERNS) for step in guided_steps):
                    failures.append((query, f"metadata leaked into guided steps: {guided_steps}"))
                    continue
                if not contains_zoom_audio_permission_guidance(guided_steps):
                    failures.append((query, f"guided steps missing microphone/speaker/permission guidance: {guided_steps}"))
                    continue
                print(f"[PASS] {query!r}")
                print(f"  article: {source_name}")
                print(f"  section: {section_heading}")
                print(f"  steps:   {guided_steps[:4]}")
                continue

            if query == "I am not getting my verification code":
                if source_name != "mfa-account-security.txt":
                    failures.append((query, f"wrong article: {source_name}"))
                    continue
                if len(guided_steps) < 3:
                    failures.append((query, f"too few guided steps: {guided_steps}"))
                    continue
                if not contains_verification_code_guidance(guided_steps):
                    failures.append((query, f"guided steps missing verification-code guidance: {guided_steps}"))
                    continue
                print(f"[PASS] {query!r}")
                print(f"  article: {source_name}")
                print(f"  section: {section_heading}")
                print(f"  steps:   {guided_steps[:4]}")
                continue

            if query == "Can I use OneDrive with my school account?":
                if source_name != "student-email-office365.txt":
                    failures.append((query, f"wrong article: {source_name}"))
                    continue
                if len(guided_steps) < 2:
                    failures.append((query, f"too few guided steps: {guided_steps}"))
                    continue
                if not contains_onedrive_guidance(guided_steps):
                    failures.append((query, f"guided steps missing OneDrive guidance: {guided_steps}"))
                    continue
                print(f"[PASS] {query!r}")
                print(f"  article: {source_name}")
                print(f"  section: {section_heading}")
                print(f"  steps:   {guided_steps[:4]}")
                continue

            if query == "Where is OBL located?":
                if source_name != "online-blended-learning.txt":
                    failures.append((query, f"wrong article: {source_name}"))
                    continue
                if not guided_steps:
                    failures.append((query, f"no guided steps: {guided_steps}"))
                    continue
                if not contains_location_guidance(guided_steps):
                    failures.append((query, f"guided steps missing location guidance: {guided_steps}"))
                    continue
                print(f"[PASS] {query!r}")
                print(f"  article: {source_name}")
                print(f"  section: {section_heading}")
                print(f"  steps:   {guided_steps[:4]}")
                continue

            if query == "Who can help with online course design?":
                if source_name != "online-blended-learning.txt":
                    failures.append((query, f"wrong article: {source_name}"))
                    continue
                if not guided_steps:
                    failures.append((query, f"no guided steps: {guided_steps}"))
                    continue
                if not contains_obl_contact_guidance(guided_steps):
                    failures.append((query, f"guided steps missing OBL contact guidance: {guided_steps}"))
                    continue
                print(f"[PASS] {query!r}")
                print(f"  article: {source_name}")
                print(f"  section: {section_heading}")
                print(f"  steps:   {guided_steps[:4]}")
                continue

            if query == "Connect to Wi-Fi":
                if source_name != "wifi-troubleshooting.txt":
                    failures.append((query, f"wrong article: {source_name}"))
                    continue
                if len(guided_steps) < 3:
                    failures.append((query, f"too few guided steps: {guided_steps}"))
                    continue
                if any(any(label in step for label in METADATA_PATTERNS) for step in guided_steps):
                    failures.append((query, f"metadata leaked into guided steps: {guided_steps}"))
                    continue
                if not contains_wifi_portal_guidance(guided_steps):
                    failures.append((query, f"guided steps missing splash/sign-in guidance: {guided_steps}"))
                    continue
                print(f"[PASS] {query!r}")
                print(f"  article: {source_name}")
                print(f"  section: {section_heading}")
                print(f"  steps:   {guided_steps[:4]}")
                continue

            if query in {
                "how do i connect to the internet?",
                "how do i connect to wifi?",
                "what wifi do students use?",
            }:
                if source_name != "wifi-troubleshooting.txt":
                    failures.append((query, f"wrong article: {source_name}"))
                    continue
                if support_title != "Student Wi-Fi Setup":
                    failures.append((query, f"wrong setup title: {support_title}"))
                    continue
                if len(guided_steps) < 5:
                    failures.append((query, f"too few setup steps: {guided_steps}"))
                    continue
                if not contains_wifi_setup_guidance(guided_steps):
                    failures.append((query, f"setup steps missing beginner Wi-Fi guidance: {guided_steps}"))
                    continue
                if has_repeated_step_text(guided_steps):
                    failures.append((query, f"duplicate setup steps: {guided_steps}"))
                    continue
                if not has_sequential_rendered_step_numbers(body):
                    failures.append((query, f"rendered step numbers were not sequential: {extract_guided_step_numbers(body)}"))
                    continue
                if body.count("Contact the CCA IT Helpdesk if the issue continues after trying these steps.") > 1:
                    failures.append((query, "deduplicated escalation sentence rendered more than once"))
                    continue
                if not any("if you do not see cca-students" in step.lower() for step in (context.get("additional_steps") or [])):
                    failures.append((query, f"setup follow-up missing network-not-visible branch: {context.get('additional_steps')}"))
                    continue
                print(f"[PASS] {query!r}")
                print(f"  article: {source_name}")
                print(f"  section: {section_heading}")
                print(f"  steps:   {guided_steps[:4]}")
                continue

            if query == "wifi not working":
                if source_name != "wifi-troubleshooting.txt":
                    failures.append((query, f"wrong article: {source_name}"))
                    continue
                if support_title != "Wi-Fi or Internet Not Working":
                    failures.append((query, f"wrong troubleshooting title: {support_title}"))
                    continue
                if not guided_steps or contains_wifi_setup_guidance(guided_steps):
                    failures.append((query, f"troubleshooting query returned setup-only guidance: {guided_steps}"))
                    continue
                if not any("open a browser" in step.lower() or "open a web browser" in step.lower() for step in guided_steps):
                    failures.append((query, f"troubleshooting steps missing concrete website test: {guided_steps}"))
                    continue
                print(f"[PASS] {query!r}")
                print(f"  article: {source_name}")
                print(f"  section: {section_heading}")
                print(f"  steps:   {guided_steps[:4]}")
                continue

            if query == "i am connected to wifi but websites do not load":
                if source_name != "wifi-troubleshooting.txt":
                    failures.append((query, f"wrong article: {source_name}"))
                    continue
                if support_title != "Connected to Wi-Fi, but Websites Do Not Load":
                    failures.append((query, f"wrong connected/no-internet title: {support_title}"))
                    continue
                if not contains_wifi_connected_no_internet_guidance(guided_steps):
                    failures.append((query, f"connected/no-internet steps missing consent/browser guidance: {guided_steps}"))
                    continue
                print(f"[PASS] {query!r}")
                print(f"  article: {source_name}")
                print(f"  section: {section_heading}")
                print(f"  steps:   {guided_steps[:4]}")
                continue

            if query == "i do not see CCA-Students":
                if source_name != "wifi-troubleshooting.txt":
                    failures.append((query, f"wrong article: {source_name}"))
                    continue
                if support_title != "CCA-Students Is Not Showing":
                    failures.append((query, f"wrong network-not-visible title: {support_title}"))
                    continue
                if not contains_wifi_not_visible_guidance(guided_steps):
                    failures.append((query, f"network-not-visible steps missing Wi-Fi list guidance: {guided_steps}"))
                    continue
                print(f"[PASS] {query!r}")
                print(f"  article: {source_name}")
                print(f"  section: {section_heading}")
                print(f"  steps:   {guided_steps[:4]}")
                continue

            if query == "my wifi password does not work":
                if source_name != "wifi-troubleshooting.txt":
                    failures.append((query, f"wrong article: {source_name}"))
                    continue
                if support_title != "Wi-Fi Password Help":
                    failures.append((query, f"wrong password title: {support_title}"))
                    continue
                if not contains_wifi_password_guidance(guided_steps):
                    failures.append((query, f"password steps missing CCA-Students/no-password guidance: {guided_steps}"))
                    continue
                if "Wi-Fi or Internet Not Working" == support_title:
                    failures.append((query, "password issue was treated as generic Wi-Fi troubleshooting"))
                    continue
                print(f"[PASS] {query!r}")
                print(f"  article: {source_name}")
                print(f"  section: {section_heading}")
                print(f"  steps:   {guided_steps[:4]}")
                continue

            if query == "Student email not working":
                if source_name != "student-email-troubleshooting.txt":
                    failures.append((query, f"wrong article: {source_name}"))
                    continue
                if section_heading == "Accessing student email:":
                    failures.append((query, "setup section returned instead of troubleshooting"))
                    continue
                if len(guided_steps) < 3:
                    failures.append((query, f"too few guided steps: {guided_steps}"))
                    continue
                if any(any(label in step for label in METADATA_PATTERNS) for step in guided_steps):
                    failures.append((query, f"metadata leaked into guided steps: {guided_steps}"))
                    continue
                if not contains_email_troubleshooting(guided_steps):
                    failures.append((query, f"guided steps missing troubleshooting guidance: {guided_steps}"))
                    continue
                if not contains_email_verification_guidance(guided_steps):
                    failures.append((query, f"guided steps missing Authenticator/MFA verification guidance: {guided_steps}"))
                    continue
                if not contains_email_primary_duo_step(guided_steps):
                    failures.append((query, f"guided steps missing Authenticator/MFA approve/prompt step: {guided_steps}"))
                    continue
                if not contains_email_web_access_guidance(guided_steps):
                    failures.append((query, f"guided steps missing Outlook web guidance: {guided_steps}"))
                    continue
                if contains_email_onboarding(guided_steps):
                    failures.append((query, f"setup/onboarding steps leaked into troubleshooting response: {guided_steps}"))
                    continue
                print(f"[PASS] {query!r}")
                print(f"  article: {source_name}")
                print(f"  section: {section_heading}")
                print(f"  steps:   {guided_steps[:4]}")
                continue

            if source_name != "classroom-technology.txt":
                failures.append((query, f"wrong article: {source_name}"))
                continue

            if query == "Projector has no signal" and "The room number." not in body:
                failures.append((query, "projector help box missing room number guidance"))
                continue

            if len(guided_steps) < 3:
                failures.append((query, f"too few guided steps: {guided_steps}"))
                continue

            if any(any(label in step for label in METADATA_PATTERNS) for step in guided_steps):
                failures.append((query, f"metadata leaked into guided steps: {guided_steps}"))
                continue

            if all(is_heading_only(step) for step in guided_steps):
                failures.append((query, f"guided steps contain only headings: {guided_steps}"))
                continue

            if not contains_guidance(guided_steps):
                failures.append((query, f"guided steps missing display/projector/source guidance: {guided_steps}"))
                continue

            if not escalation_text.strip():
                failures.append((query, "missing escalation text"))
                continue

            print(f"[PASS] {query!r}")
            print(f"  article: {source_name}")
            print(f"  section: {section_heading}")
            print(f"  steps:   {guided_steps[:4]}")

        evaluate_agent_metadata_rendering(client, failures)

    print()
    total_cases = (
        len(QUERIES)
        + len(INPUT_GUARD_CASES)
        + len(CONTACT_CASES)
        + len(WEAK_QUERY_CASES)
        + len(D2L_ACCESS_CASES)
        + 3
        + len(ZOOM_SSO_CASES)
        + len(PRINTING_CASES)
        + len(MFA_CLARIFICATION_CASES)
        + len(MFA_AUTHENTICATOR_CASES)
        + 1
    )
    print(f"Total cases: {total_cases}")
    print(f"Passed:      {total_cases - len(failures)}")
    print(f"Failed:      {len(failures)}")

    if failures:
        print("\nFailures:")
        for query, error in failures:
            print(f"- {query!r}")
            print(f"  {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
