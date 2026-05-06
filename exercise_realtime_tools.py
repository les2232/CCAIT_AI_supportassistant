import json

from realtime_tools import (
    log_support_interaction,
    prepare_it_ticket,
    search_support_kb,
)


def main():
    examples = {
        "search_support_kb_wifi": search_support_kb("I can’t connect to Wi-Fi"),
        "search_support_kb_mfa": search_support_kb("My MFA is not working"),
        "prepare_it_ticket": prepare_it_ticket(
            issue_summary="Student cannot connect to campus Wi-Fi after joining CCA-Students.",
            category="wifi",
            location="CentreTech campus library",
            device="Windows 11 laptop, Chrome",
            error_message="Wi-Fi says connected but no internet",
            steps_tried="Reconnected to CCA-Students and reopened a browser to trigger the sign-in page.",
            resolved=False,
        ),
        "log_support_interaction": log_support_interaction(
            user_question="My MFA is not working",
            category="mfa",
            resolved=False,
            escalated=True,
            notes="Caller could not approve the MFA prompt after changing phones.",
        ),
    }

    print(json.dumps(examples, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
