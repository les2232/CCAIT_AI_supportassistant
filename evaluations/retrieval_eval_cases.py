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
        "question": "My MFA is not working",
        "expected_article": "mfa-account-security.txt",
        "expected_heading": "Common MFA problems:",
        "acceptable_headings": [
            "Common MFA problems:",
            "Changed phones or lost MFA access:",
        ],
    },
    {
        "question": "verification code is not working",
        "expected_article": None,
        "expected_heading": None,
    },
    {
        "question": "I changed phones and cannot approve MFA",
        "expected_article": "mfa-account-security.txt",
        "expected_heading": "Changed phones or lost MFA access:",
        "acceptable_headings": [
            "Changed phones or lost MFA access:",
            "Common MFA problems:",
        ],
    },
    {
        "question": "I lost my phone and can't do MFA",
        "expected_article": "mfa-account-security.txt",
        "expected_heading": "Changed phones or lost MFA access:",
    },
    {
        "question": "Duo keeps asking me again",
        "expected_article": None,
        "expected_heading": None,
    },
    {
        "question": "Duo keeps prompting me",
        "expected_article": None,
        "expected_heading": None,
    },
    {
        "question": "Duo verification is not working",
        "expected_article": None,
        "expected_heading": None,
    },
    {
        "question": "MFA keeps asking me",
        "expected_article": "mfa-account-security.txt",
        "expected_heading": "Common MFA problems:",
    },
    {
        "question": "Microsoft Authenticator is not working",
        "expected_article": "mfa-account-security.txt",
        "expected_heading": "Common MFA problems:",
    },
    {
        "question": "add alternate MFA method",
        "expected_article": "mfa-account-security.txt",
        "expected_heading": "Adding an alternate MFA method:",
    },
    {
        "question": "Authenticator app not working",
        "expected_article": "mfa-account-security.txt",
        "expected_heading": "Common MFA problems:",
    },
    {
        "question": "Duo not working",
        "expected_article": None,
        "expected_heading": None,
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
        "expected_article": "d2l.txt",
        "expected_heading": "How to access:",
        "acceptable_headings": [
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
        "expected_heading": "How to access:",
        "acceptable_headings": [
            "How to access:",
            "Where to get help:",
        ],
    },
    {
        "question": "How do I find my school email address?",
        "expected_article": "student-email.txt",
        "expected_heading": "Accessing student email:",
        "acceptable_headings": [
            "Accessing student email:",
            "Finding your student email address:",
        ],
    },
    {
        "question": "How do I access student email?",
        "expected_article": "student-email.txt",
        "expected_heading": "Accessing student email:",
        "acceptable_headings": [
            "Accessing student email:",
            "Alternative access:",
        ],
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
        "expected_heading": "Cannot connect to CCA Wi-Fi:",
    },
    {
        "question": "how do i connect to the internet?",
        "expected_article": "wifi-troubleshooting.txt",
        "expected_heading": "First-time setup:",
        "acceptable_headings": [
            "First-time setup:",
            "Connect to Wi-Fi:",
        ],
    },
    {
        "question": "how do i connect to wifi?",
        "expected_article": "wifi-troubleshooting.txt",
        "expected_heading": "First-time setup:",
        "acceptable_headings": [
            "First-time setup:",
            "Connect to Wi-Fi:",
        ],
    },
    {
        "question": "what wifi do students use?",
        "expected_article": "wifi-troubleshooting.txt",
        "expected_heading": "CCA student Wi-Fi network name:",
    },
    {
        "question": "wifi not working",
        "expected_article": "wifi-troubleshooting.txt",
        "expected_heading": "Internet or network not working:",
        "acceptable_headings": [
            "Internet or network not working:",
            "Cannot connect to CCA Wi-Fi:",
        ],
    },
    {
        "question": "i am connected to wifi but websites do not load",
        "expected_article": "wifi-troubleshooting.txt",
        "expected_heading": "If you are connected but websites do not load:",
    },
    {
        "question": "i do not see CCA-Students",
        "expected_article": "wifi-troubleshooting.txt",
        "expected_heading": "If you do not see CCA-Students:",
    },
    {
        "question": "my wifi password does not work",
        "expected_article": "wifi-troubleshooting.txt",
        "expected_heading": "If your password does not work:",
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
        "expected_heading": "Projector has no signal:",
        "acceptable_headings": [
            "Projector has no signal:",
            "Where to get help / When to contact IT:",
        ],
    },
    {
        "question": "Who do I contact for classroom technology help?",
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
        "question": "how do I map a printer",
        "expected_article": "printing.txt",
        "expected_heading": "Printing from campus computers:",
    },
    {
        "question": "how do I add a printer",
        "expected_article": "printing.txt",
        "expected_heading": "Printing from campus computers:",
    },
    {
        "question": "printer not showing",
        "expected_article": "printing.txt",
        "expected_heading": "Common issues: printer not showing or print job not going through:",
    },
    {
        "question": "the printer says error",
        "expected_article": "printing.txt",
        "expected_heading": "Printer error message:",
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
        "expected_article": "mfa-account-security.txt",
        "expected_heading": "Changed phones or lost MFA access:",
        "acceptable_headings": [
            "Common MFA problems:",
            "MFA or verification problems:",
            "Changed phones or lost MFA access:",
        ],
    },
    {
        "question": "I am not getting my verification code",
        "expected_article": "mfa-account-security.txt",
        "expected_heading": "Common MFA problems:",
        "acceptable_headings": [
            "Common MFA problems:",
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
        "question": "Zoom SSO login",
        "expected_article": "zoom-support.txt",
        "expected_heading": "Sign-in problems:",
    },
    {
        "question": "Zoom asks for SSO",
        "expected_article": "zoom-support.txt",
        "expected_heading": "Sign-in problems:",
    },
    {
        "question": "what is the Zoom company domain",
        "expected_article": "zoom-support.txt",
        "expected_heading": "Sign-in problems:",
    },
    {
        "question": "Zoom license not showing",
        "expected_article": "zoom-support.txt",
        "expected_heading": "Sign-in problems:",
    },
    {
        "question": "Zoom not working",
        "expected_article": "zoom-support.txt",
        "expected_heading": "Zoom not working:",
        "acceptable_headings": [
            "Zoom not working:",
            "Zoom audio not working:",
            "App or browser:",
            "Audio or video problems:",
        ],
    },
    {
        "question": "My Zoom audio is not working",
        "expected_article": "zoom-support.txt",
        "expected_heading": "Zoom audio not working:",
        "acceptable_headings": [
            "Zoom audio not working:",
            "Audio or video problems:",
            "Joining Zoom classes:",
            "Still need help with Zoom?:",
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
        "expected_heading": "Still need help with Zoom?:",
        "acceptable_headings": [
            "When to contact OBL:",
            "Still need help with Zoom?:",
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
        "question": "Student email not working",
        "expected_article": "student-email-troubleshooting.txt",
        "expected_heading": "Student email not working:",
        "acceptable_headings": [
            "Student email not working:",
            "Cannot access student email:",
        ],
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
