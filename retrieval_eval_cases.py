"""
Representative section-retrieval test cases for the AI IT Support Assistant.

These are hand-authored evaluation examples based on the current support
articles and retrieval behavior. They are not real user logs.
"""

RETRIEVAL_EVAL_CASES = [
    {
        "question": "How do I reset my password?",
        "expected_article": "password-reset.txt",
        "expected_heading": "How to reset your password:",
    },
    {
        "question": "My MFA verification code is not working",
        "expected_article": "mfa-account-security.txt",
        "expected_heading": "Common MFA problems:",
        "acceptable_headings": [
            "Common MFA problems:",
            "MFA or verification problems:",
        ],
    },
    {
        "question": "How do I access D2L?",
        "expected_article": "d2l-troubleshooting.txt",
        "expected_heading": "Cannot access D2L or log into D2L:",
        "acceptable_headings": [
            "Cannot access D2L or log into D2L:",
            "How to access:",
        ],
    },
    {
        "question": "Where do I submit assignments?",
        "expected_article": "d2l-troubleshooting.txt",
        "expected_heading": "Assignment upload problems:",
        "acceptable_headings": [
            "Assignment upload problems:",
            "What students use it for:",
        ],
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
        "question": "I cannot connect to CCA Wi-Fi",
        "expected_article": "wifi-troubleshooting.txt",
        "expected_heading": "General guidance",
    },
    {
        "question": "I need help with a Zoom meeting",
        "expected_article": "zoom-support.txt",
        "expected_heading": "Joining Zoom classes:",
        "acceptable_headings": [
            "Joining Zoom classes:",
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
        "expected_article": "printing.txt",
        "expected_heading": "Where students can print:",
        "acceptable_headings": [
            "What this helps with:",
            "Where students can print:",
            "Printing from campus computers:",
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
    {
        "question": "Can I print from my laptop at CCA?",
        "expected_article": "printing.txt",
        "expected_heading": "Printing from personal devices:",
    },
    {
        "question": "The printer is not showing on my computer",
        "expected_article": "printing.txt",
        "expected_heading": "Common issues: printer not showing or print job not going through:",
        "acceptable_headings": [
            "Common issues: printer not showing or print job not going through:",
            "Printing from campus computers:",
        ],
    },
    {
        "question": "Who can help me with printing problems at CCA?",
        "expected_article": "printing.txt",
        "expected_heading": "When to contact IT:",
        "acceptable_headings": [
            "When to contact IT:",
            "CCA IT Helpdesk:",
            "Printing from personal devices:",
        ],
    },
    {
        "question": "How do I set up MFA for my CCA account?",
        "expected_article": "mfa-account-security.txt",
        "expected_heading": "Setting up MFA:",
    },
    {
        "question": "I changed phones and cannot complete MFA",
        "expected_article": "password-reset.txt",
        "expected_heading": "MFA or verification problems:",
        "acceptable_headings": [
            "Common MFA problems:",
            "MFA or verification problems:",
        ],
    },
    {
        "question": "I am not getting my verification code",
        "expected_article": "password-reset.txt",
        "expected_heading": "MFA or verification problems:",
        "acceptable_headings": [
            "Common MFA problems:",
            "MFA or verification problems:",
        ],
    },
    {
        "question": "What does MFA affect at CCA?",
        "expected_article": "mfa-account-security.txt",
        "expected_heading": "What MFA affects:",
    },
    {
        "question": "How do I join a Zoom class at CCA?",
        "expected_article": "zoom-support.txt",
        "expected_heading": "Joining Zoom classes:",
    },
    {
        "question": "My Zoom audio is not working",
        "expected_article": "zoom-support.txt",
        "expected_heading": "Audio or video problems:",
        "acceptable_headings": [
            "Audio or video problems:",
            "Joining Zoom classes:",
            "When to contact IT for Zoom help:",
        ],
    },
    {
        "question": "Should I use the Zoom app or browser?",
        "expected_article": "zoom-support.txt",
        "expected_heading": "App or browser:",
    },
    {
        "question": "Who do I contact for Zoom help at CCA?",
        "expected_article": "zoom-support.txt",
        "expected_heading": "When to contact IT for Zoom help:",
        "acceptable_headings": [
            "When to contact OBL:",
            "When to contact IT for Zoom help:",
            "Joining Zoom classes:",
        ],
    },
    {
        "question": "I cannot log into D2L at CCA",
        "expected_article": "d2l-troubleshooting.txt",
        "expected_heading": "Cannot access D2L or log into D2L:",
        "acceptable_headings": [
            "Cannot access D2L or log into D2L:",
            "MyCourses / D2L (Canvas) Support — What to know:",
        ],
    },
    {
        "question": "My class is not showing in D2L",
        "expected_article": "d2l-troubleshooting.txt",
        "expected_heading": "Course not showing:",
        "acceptable_headings": [
            "Course not showing:",
            "When to contact your instructor:",
        ],
    },
    {
        "question": "My D2L assignment upload is not working",
        "expected_article": "d2l-troubleshooting.txt",
        "expected_heading": "Assignment upload problems:",
    },
    {
        "question": "When should I contact my instructor for D2L?",
        "expected_article": "d2l-troubleshooting.txt",
        "expected_heading": "When to contact your instructor:",
        "acceptable_headings": [
            "When to contact your instructor:",
            "Course not showing:",
            "Assignment upload problems:",
            "When to contact IT:",
        ],
    },
    {
        "question": "I cannot access my student email at CCA",
        "expected_article": "student-email-troubleshooting.txt",
        "expected_heading": "Cannot access student email:",
    },
    {
        "question": "Outlook keeps asking for my password",
        "expected_article": "student-email-troubleshooting.txt",
        "expected_heading": "Outlook keeps asking for my password:",
    },
    {
        "question": "My student email keeps sending me back to verification",
        "expected_article": "student-email-troubleshooting.txt",
        "expected_heading": "MFA or verification loop:",
        "acceptable_headings": [
            "MFA or verification loop:",
            "Accessing student email:",
        ],
    },
    {
        "question": "Should I use Outlook on the web or the app?",
        "expected_article": "student-email-troubleshooting.txt",
        "expected_heading": "Outlook app or web access:",
    },
    {
        "question": "When should I contact IT for student email problems?",
        "expected_article": "student-email-troubleshooting.txt",
        "expected_heading": "When to contact IT for student email help:",
        "acceptable_headings": [
            "When to contact IT for student email help:",
            "CCA IT Helpdesk:",
            "Accessing student email:",
        ],
    },
]
