"""
Representative section-retrieval test cases for the AI IT Support Assistant.

These are hand-authored evaluation examples based on the current support
articles and retrieval behavior. They are not real user logs.
"""

RETRIEVAL_EVAL_CASES = [
    {
        "question": "How do I reset my password?",
        "expected_article": "password-reset.txt",
        "expected_heading": "General guidance",
    },
    {
        "question": "My MFA verification code is not working",
        "expected_article": "password-reset.txt",
        "expected_heading": "General guidance",
    },
    {
        "question": "How do I access D2L?",
        "expected_article": "d2l.txt",
        "expected_heading": "How to access:",
    },
    {
        "question": "Where do I submit assignments?",
        "expected_article": "d2l.txt",
        "expected_heading": "What students use it for:",
    },
    {
        "question": "I can't access my course materials",
        "expected_article": "d2l.txt",
        "expected_heading": "Where to get help:",
    },
    {
        "question": "How do I find my school email address?",
        "expected_article": "student-email.txt",
        "expected_heading": "Accessing student email:",
    },
    {
        "question": "How do I log into MyCCA?",
        "expected_article": "student-email.txt",
        "expected_heading": "MyCCA login:",
    },
    {
        "question": "What are the student email password rules?",
        "expected_article": "student-email.txt",
        "expected_heading": "Password requirements:",
    },
    {
        "question": "How do I get a semester laptop?",
        "expected_article": "student-laptops-calculators.txt",
        "expected_heading": "How to get a semester laptop:",
    },
    {
        "question": "Where do I check out a graphing calculator?",
        "expected_article": "student-laptops-calculators.txt",
        "expected_heading": "How to get a calculator:",
    },
    {
        "question": "Who can borrow a laptop for the semester?",
        "expected_article": "student-laptops-calculators.txt",
        "expected_heading": "Who is eligible:",
        "acceptable_headings": [
            "Who is eligible:",
            "How to get a semester laptop:",
        ],
    },
    {
        "question": "My wifi connection keeps dropping",
        "expected_article": "wifi-troubleshooting.txt",
        "expected_heading": "General guidance",
    },
    {
        "question": "I need help with a Zoom meeting",
        "expected_article": "online-blended-learning.txt",
        "expected_heading": "Learning technology support:",
        "acceptable_headings": [
            "Learning technology support:",
            "Where to get help / When to contact OBL or IT:",
        ],
    },
    {
        "question": "Who do I contact for online learning design support?",
        "expected_article": "online-blended-learning.txt",
        "expected_heading": "Where to get help / When to contact OBL or IT:",
    },
    {
        "question": "Where is the OBL office located?",
        "expected_article": "online-blended-learning.txt",
        "expected_heading": "Location:",
    },
    {
        "question": "How do I print on campus?",
        "expected_article": "cca-tech-help.txt",
        "expected_heading": "Printing Help / Hub Printers — What this is:",
        "acceptable_headings": [
            "Printing Help / Hub Printers — What this is:",
            "Printing Help / Hub Printers — Where to go for help:",
        ],
    },
    {
        "question": "Where can I borrow headphones?",
        "expected_article": "cca-tech-help.txt",
        "expected_heading": "Loan Headphones — What this is:",
        "acceptable_headings": [
            "Loan Headphones — What this is:",
            "Loan Headphones — Where to go:",
        ],
    },
    {
        "question": "Can you help with Adobe software availability?",
        "expected_article": "cca-tech-help.txt",
        "expected_heading": "Software Availability (Adobe, SolidWorks, Coding Software) — What this is:",
        "acceptable_headings": [
            "Software Availability (Adobe, SolidWorks, Coding Software) — What this is:",
            "Software Availability (Adobe, SolidWorks, Coding Software) — Where to go for more:",
        ],
    },
    {
        "question": "The projector in my classroom is not working",
        "expected_article": "classroom-technology.txt",
        "expected_heading": "Where to get help / When to contact IT:",
    },
    {
        "question": "What classroom technology upgrades are available?",
        "expected_article": "classroom-technology.txt",
        "expected_heading": "Classroom technology upgrades include:",
    },
    {
        "question": "I can't access YuJa videos in my course",
        "expected_article": "yuja-panorama.txt",
        "expected_heading": "Student support and access:",
    },
    {
        "question": "Who do I contact about YuJa accessibility problems?",
        "expected_article": "yuja-panorama.txt",
        "expected_heading": "Where to get help / When to contact support:",
    },
    {
        "question": "I need Windows 11 upgrade help",
        "expected_article": "windows-11.txt",
        "expected_heading": "Common issues or things to know:",
        "acceptable_headings": [
            "Common issues or things to know:",
            "Where to get help / When to contact IT:",
        ],
    },
    {
        "question": "How long does the Windows 11 upgrade take?",
        "expected_article": "windows-11.txt",
        "expected_heading": "Common issues or things to know:",
    },
    {
        "question": "",
        "expected_article": None,
        "expected_heading": None,
    },
    {
        "question": "help",
        "expected_article": None,
        "expected_heading": None,
    },
    {
        "question": "Parking permit help",
        "expected_article": None,
        "expected_heading": None,
    },
]
