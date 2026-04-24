"""
Pilot-ready evaluation cases for realistic student and faculty support questions.

Each case documents:
- question: realistic user wording
- expected_behavior: direct or disambiguation
- expected_article: expected matched article for direct cases
- expected_options: expected disambiguation labels for ambiguous cases
- notes: what this case is intended to validate
"""

PILOT_EVAL_CASES = [
    {"question": "How do I reset my password?", "expected_behavior": "direct", "expected_article": "password-reset.txt", "notes": "student password reset"},
    {"question": "My account is locked", "expected_behavior": "direct", "expected_article": "password-reset.txt", "notes": "account lockout support"},
    {"question": "I changed phones and cannot verify my login", "expected_behavior": "direct", "expected_article": "mfa-account-security.txt", "notes": "MFA device-change support"},
    {"question": "How do I set up MFA for my account?", "expected_behavior": "direct", "expected_article": "mfa-account-security.txt", "notes": "MFA setup"},
    {"question": "I am not getting my verification code", "expected_behavior": "direct", "expected_article": "password-reset.txt", "notes": "verification issue escalation"},
    {"question": "How do I access D2L?", "expected_behavior": "direct", "expected_article": "d2l-troubleshooting.txt", "notes": "D2L login/access"},
    {"question": "My class is not showing in D2L", "expected_behavior": "direct", "expected_article": "d2l-troubleshooting.txt", "notes": "missing course"},
    {"question": "My assignment will not upload in D2L", "expected_behavior": "direct", "expected_article": "d2l-troubleshooting.txt", "notes": "assignment upload issue"},
    {"question": "Where do I submit assignments?", "expected_behavior": "direct", "expected_article": "d2l-troubleshooting.txt", "notes": "student course workflow"},
    {"question": "Student email not working", "expected_behavior": "direct", "expected_article": "student-email.txt", "notes": "broad student email access"},
    {"question": "Outlook keeps asking for my password", "expected_behavior": "direct", "expected_article": "student-email-troubleshooting.txt", "notes": "email troubleshooting"},
    {"question": "How do I find my school email address?", "expected_behavior": "direct", "expected_article": "student-email.txt", "notes": "student email lookup"},
    {"question": "Can I use OneDrive with my school account?", "expected_behavior": "direct", "expected_article": "student-email-office365.txt", "notes": "Microsoft 365 / OneDrive usage"},
    {"question": "How do I connect to Wi-Fi?", "expected_behavior": "direct", "expected_article": "wifi-troubleshooting.txt", "notes": "basic Wi-Fi help"},
    {"question": "Wi-Fi keeps dropping on my laptop", "expected_behavior": "direct", "expected_article": "wifi-troubleshooting.txt", "notes": "unstable wireless connection"},
    {"question": "How do I print on campus?", "expected_behavior": "direct", "expected_article": "printing.txt", "notes": "campus printing"},
    {"question": "Can I print from my laptop at CCA?", "expected_behavior": "direct", "expected_article": "printing.txt", "notes": "personal device printing"},
    {"question": "Who can help me with printing problems at CCA?", "expected_behavior": "direct", "expected_article": "printing.txt", "notes": "printing escalation path"},
    {"question": "How do I get a semester laptop?", "expected_behavior": "direct", "expected_article": "student-laptops-calculators.txt", "notes": "laptop loan"},
    {"question": "Where do I check out a graphing calculator?", "expected_behavior": "direct", "expected_article": "student-laptops-calculators.txt", "notes": "calculator checkout"},
    {"question": "Where can I borrow headphones?", "expected_behavior": "direct", "expected_article": "cca-tech-help.txt", "notes": "broad support directory item"},
    {"question": "Can you help with Adobe software availability?", "expected_behavior": "direct", "expected_article": "cca-tech-help.txt", "notes": "software availability routing"},
    {"question": "How do I join a Zoom class?", "expected_behavior": "direct", "expected_article": "zoom-support.txt", "notes": "student Zoom entry point"},
    {"question": "Zoom not working", "expected_behavior": "direct", "expected_article": "zoom-support.txt", "notes": "broad Zoom support should still land on Zoom help"},
    {"question": "I can't access YuJa videos in my course", "expected_behavior": "direct", "expected_article": "yuja-panorama.txt", "notes": "course videos access"},
    {"question": "Who do I contact about YuJa accessibility problems?", "expected_behavior": "direct", "expected_article": "yuja-panorama.txt", "notes": "YuJa escalation"},
    {"question": "Where is OBL located?", "expected_behavior": "direct", "expected_article": "online-blended-learning.txt", "notes": "OBL location lookup"},
    {"question": "Who can help with online course design?", "expected_behavior": "direct", "expected_article": "online-blended-learning.txt", "notes": "faculty instructional support"},
    {"question": "Classroom display won’t turn on", "expected_behavior": "direct", "expected_article": "classroom-technology.txt", "notes": "faculty classroom AV support"},
    {"question": "Projector has no signal", "expected_behavior": "direct", "expected_article": "classroom-technology.txt", "notes": "classroom projector issue"},
    {"question": "Audio not working in classroom", "expected_behavior": "direct", "expected_article": "classroom-technology.txt", "notes": "classroom audio issue"},
    {"question": "I need Windows 11 upgrade help", "expected_behavior": "direct", "expected_article": "windows-11.txt", "notes": "Windows upgrade support"},
    {"question": "can't log in", "expected_behavior": "disambiguation", "expected_options": ["D2L", "Email", "Account"], "notes": "generic login ambiguity"},
    {"question": "can't access my class", "expected_behavior": "disambiguation", "expected_options": ["D2L", "Email", "Zoom", "Course videos"], "notes": "class access ambiguity"},
    {"question": "nothing is working", "expected_behavior": "disambiguation", "expected_options": ["Wi-Fi", "D2L", "Email", "Zoom", "I'm not sure"], "notes": "very broad support ambiguity"},
    {"question": "can't open anything", "expected_behavior": "disambiguation", "expected_options": ["D2L", "Email", "Zoom", "Course videos", "I'm not sure"], "notes": "very broad access ambiguity"},
    {"question": "problem with login", "expected_behavior": "disambiguation", "expected_options": ["D2L", "Email", "Account"], "notes": "generic login wording"},
    {"question": "I need help finding the right IT support option", "expected_behavior": "direct", "expected_article": "cca-tech-help.txt", "notes": "safe broad support routing"},
]
