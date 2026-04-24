"""
Representative routing test cases for the AI IT Support Assistant.

These are hand-authored evaluation examples based on the current support
articles and router behavior. They are not real user logs.
"""

ROUTING_EVAL_CASES = [
    {"category": "password", "question": "How do I reset my password?", "expected": "password-reset.txt"},
    {"category": "password", "question": "I forgot my MyCCA password", "expected": "password-reset.txt"},
    {"category": "password", "question": "My MFA is not working", "expected": "password-reset.txt"},
    {"category": "password", "question": "My account is locked", "expected": "password-reset.txt"},
    {"category": "password", "question": "I can't sign in to MyCCA", "expected": "password-reset.txt"},
    {"category": "password", "question": "The verification code is not working when I log in", "expected": "password-reset.txt"},
    {"category": "password", "question": "Need help unlocking my account", "expected": "password-reset.txt"},
    {"category": "password", "question": "My authenticator app is not letting me in", "expected": "password-reset.txt"},

    {"category": "wifi", "question": "Wi-Fi keeps dropping on my laptop", "expected": "wifi-troubleshooting.txt"},
    {"category": "wifi", "question": "Campus wifi won't connect", "expected": "wifi-troubleshooting.txt"},
    {"category": "wifi", "question": "The wireless network is not working", "expected": "wifi-troubleshooting.txt"},
    {"category": "wifi", "question": "I have no internet on campus", "expected": "wifi-troubleshooting.txt"},
    {"category": "wifi", "question": "My network connection is unstable", "expected": "wifi-troubleshooting.txt"},
    {"category": "wifi", "question": "How do I join the student wifi?", "expected": "wifi-troubleshooting.txt"},
    {"category": "wifi", "question": "My laptop connects to wifi but there is no internet", "expected": "wifi-troubleshooting.txt"},
    {"category": "wifi", "question": "Wireless access is failing in the library", "expected": "wifi-troubleshooting.txt"},

    {"category": "d2l", "question": "I can't get into my online class", "expected": "d2l.txt"},
    {"category": "d2l", "question": "Where do I find my assignments?", "expected": "d2l.txt"},
    {"category": "d2l", "question": "Where do I submit assignments?", "expected": "d2l.txt"},
    {"category": "d2l", "question": "How do I submit homework in Brightspace?", "expected": "d2l.txt"},
    {"category": "d2l", "question": "My course materials are missing", "expected": "d2l.txt"},
    {"category": "d2l", "question": "How do I open D2L?", "expected": "d2l.txt"},
    {"category": "d2l", "question": "I need help with my online course", "expected": "d2l.txt"},
    {"category": "d2l", "question": "Where are my quizzes?", "expected": "d2l.txt"},
    {"category": "d2l", "question": "I can't access Brightspace", "expected": "d2l.txt"},
    {"category": "d2l", "question": "How do I get to my class materials?", "expected": "d2l.txt"},

    {"category": "email", "question": "How do I access student email?", "expected": "student-email.txt"},
    {"category": "email", "question": "I can't log into Outlook", "expected": "student-email.txt"},
    {"category": "email", "question": "What is my school email address?", "expected": "student-email.txt"},
    {"category": "email", "question": "Where do I find my student email?", "expected": "student-email.txt"},
    {"category": "email", "question": "How do I sign into Office 365?", "expected": "student-email.txt"},
    {"category": "email", "question": "My college email inbox is not opening", "expected": "student-email.txt"},
    {"category": "email", "question": "I need my Outlook email login", "expected": "student-email.txt"},
    {"category": "email", "question": "How do I check my CCA email?", "expected": "student-email.txt"},

    {"category": "laptop-calculator", "question": "How do I get a semester laptop?", "expected": "student-laptops-calculators.txt"},
    {"category": "laptop-calculator", "question": "Can I borrow a calculator?", "expected": "student-laptops-calculators.txt"},
    {"category": "laptop-calculator", "question": "Where do I check out a laptop?", "expected": "student-laptops-calculators.txt"},
    {"category": "laptop-calculator", "question": "I need a TI-84 for class", "expected": "student-laptops-calculators.txt"},
    {"category": "laptop-calculator", "question": "How does the laptop loan work?", "expected": "student-laptops-calculators.txt"},
    {"category": "laptop-calculator", "question": "Can students borrow graphing calculators?", "expected": "student-laptops-calculators.txt"},
    {"category": "laptop-calculator", "question": "Where is the calculator checkout desk?", "expected": "student-laptops-calculators.txt"},
    {"category": "laptop-calculator", "question": "I need to borrow a loaner laptop", "expected": "student-laptops-calculators.txt"},

    {"category": "zoom", "question": "I need help with Zoom", "expected": "online-blended-learning.txt"},
    {"category": "zoom", "question": "My Zoom link is not working", "expected": "online-blended-learning.txt"},
    {"category": "zoom", "question": "How do I join a Zoom class?", "expected": "online-blended-learning.txt"},
    {"category": "zoom", "question": "I need Zoom support for my online course", "expected": "online-blended-learning.txt"},
    {"category": "zoom", "question": "Where do I get help with a Zoom meeting?", "expected": "online-blended-learning.txt"},
    {"category": "zoom", "question": "Remote class video help", "expected": "online-blended-learning.txt"},

    {"category": "unsupported", "question": "", "expected": None},
    {"category": "unsupported", "question": "   ", "expected": None},
    {"category": "unsupported", "question": "help", "expected": None},
    {"category": "unsupported", "question": "I need tech support", "expected": None},
    {"category": "unsupported", "question": "Parking permit help", "expected": None},
    {"category": "unsupported", "question": "How do I print on campus?", "expected": None},
    {"category": "unsupported", "question": "My Windows 11 update failed", "expected": None},
    {"category": "unsupported", "question": "Need help with Microsoft Teams", "expected": None},
    {"category": "unsupported", "question": "Projector in the classroom is not working", "expected": None},
    {"category": "unsupported", "question": "Adobe won't install on my laptop", "expected": None},
    {"category": "unsupported", "question": "Can you help me with my financial aid portal?", "expected": None},
    {"category": "unsupported", "question": "I can't access YuJa videos", "expected": None},
]
