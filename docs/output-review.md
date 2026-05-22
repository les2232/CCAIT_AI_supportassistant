# Output Review Checklist

Last updated: 2026-05-22

Purpose: manual pilot review checklist for student-facing assistant output. Use this to check answer quality, tone, source grounding, and safety before pilot handoff or after KB edits.

Review posture:

- Run in deterministic KB-only mode.
- Do not enable optional OpenAI, Realtime, agent, classifier, or semantic retrieval paths for this review.
- Confirm answers cite or visibly derive from approved local KB content.
- Confirm public answers do not expose internal SOP content.
- Record observations in the Notes field before changing KB content or tests.

## Manual Review Prompts

| Prompt | Expected article / flow | Good answer should mention | Answer must avoid | Notes |
|---|---|---|---|---|
| `I can't log in` | Disambiguation flow. Options should include D2L, Student email, MyCCA, Campus computer, Wi-Fi, MFA/Auth, and "I'm not sure". | Asks which login is failing instead of guessing. Keeps choices short and student-friendly. | Must not pick password reset automatically. Must not claim a specific service is down. Must not mention internal KB. |  |
| `I can't access my class` | Disambiguation flow. Options should include D2L, Email, Zoom, Course videos. | Helps separate course access from email, Zoom, and video/media problems. | Must not assume the issue is only D2L. Must not tell the student to contact the instructor before clarifying the system. |  |
| `My student email is not working` | Direct answer from `student-email-troubleshooting.txt`. | Student email account, same password as MyCCA / CCA homepage sign-in, MFA prompt, Outlook on the web, CCA IT Helpdesk if MFA is not set up or cannot be completed. | Must not imply Microsoft Authenticator is the only MFA method. Must not claim MyCCA itself requires MFA. Must not ask for passwords or MFA codes. |  |
| `I am not getting my verification code` | Direct answer from `mfa-account-security.txt`, usually Common MFA problems. | Check expected method/device, retry code carefully, request/approve MFA prompt if available, confirm phone text/call or Authenticator method, contact CCA IT if still blocked. | Must not route to Duo-only faculty/staff guidance as the final answer. Must not ask for the code. Must not over-explain internal Entra details. |  |
| `I got a new phone and can't approve MFA` | Direct answer from `mfa-account-security.txt`, changed-phone / lost-MFA-access path. | New phone or changed number can leave MFA tied to the old method; contact CCA IT Helpdesk to update verification method or phone number. | Must not tell the student they can self-service every recovery case. Must not expose internal admin-system steps. Must not ask for secrets. |  |
| `Can I use OneDrive with my school account?` | Direct answer from `student-email-office365.txt`. | All students have Microsoft 365 web access; web access includes Outlook, OneDrive, Teams, and Office Online; desktop app access is not confirmed. | Must not promise desktop Office apps, OneDrive sync, storage quotas, or sharing limits unless verified. |  |
| `Where is OBL located?` | Direct answer from `online-blended-learning.txt`, Location section. | OBL is in room F103; go to F103 if finding OBL in person; contact OBL if unsure how to get there. | Must not confuse OBL with the Hub. Must not add an unverified building name. |  |
| `Where is the Hub?` | Direct answer from `it-resources.txt` or `cca-tech-help.txt`. | CentreTech Hub is in the Classroom Building, Room 107; phone `(303) 360-4736`; email `TheHub.cca@ccaurora.edu`; hours Monday-Thursday 8 a.m. to 6 p.m., Friday 8 a.m. to 5 p.m., Saturday 10 a.m. to 2 p.m.; many services online. | Must not confuse Hub location with OBL F103. Must not treat Hub contact info as the IT Helpdesk. Must not overclaim exact desk ownership for laptops, printing, or headphones. |  |
| `I need a laptop` | Direct answer from `student-laptops-calculators.txt`, semester laptop path. | Currently enrolled students can ask about loaner laptop availability; start with Student Success in the Student Center; availability/equipment can vary; ask about current checkout process. | Must not guarantee inventory, eligibility, renewal, or same-day checkout. Must not send account/login troubleshooting to the Hub instead of IT. |  |
| `Can I use Adobe?` | Direct answer from `cca-tech-help.txt` or `student-laptops-calculators.txt`, software availability section. | Adobe Creative Cloud products are installed on CCA Macs; access is limited to graphic design students or students whose class requires Adobe; if class requires Adobe, students should be able to sign in on a CCA Mac. | Must not imply every student has Adobe access. Must not promise personal-device install or desktop license entitlement. |  |
| `Where can I use SolidWorks?` | Direct answer from `cca-tech-help.txt` or `student-laptops-calculators.txt`, software availability section. | SolidWorks is installed on Innovation Lab computers and CAST 132 computers. | Must not claim SolidWorks is available on all Hub computers, all CCA computers, or student personal devices. |  |
| `How do I print on campus?` | Direct answer from `printing.txt`. | Students can print using campus printing resources such as Hub printers; Hub can be a starting point; use CCA IT Helpdesk for account/login/device technology problems; exact printer issue details help support. | Must not expose internal print server paths. Must not claim exact front-desk ownership unless verified. Must not promise personal-device printing will always work. |  |
| `Zoom asks for SSO` | Direct answer from `zoom-support.txt`. | Use CCA Zoom / SSO guidance from public KB; confirm CCA account sign-in and Zoom app/browser basics; contact IT/OBL according to issue type. | Must not expose old/internal company domains, Duo-only assumptions, license-sync internals, or internal SOP notes. |  |
| `I need help` | Input guard / vague-help flow. | Offers safe broad options such as Wi-Fi help, Password reset, and Contact IT. | Must not answer from a random article. Must not ask for sensitive information. Must not expose internal KB. |  |

## General Output Review Criteria

For each prompt, confirm:

- The article or disambiguation flow matches the expected support path.
- The title and summary are student-friendly and not overly technical.
- The first four guided steps are useful on their own.
- Escalation is clear when the student is blocked.
- Phone numbers, emails, locations, service availability, and eligibility claims match `docs/content-verification.md`.
- Public answers do not include internal SOP content, server names, internal ticket notes, or admin-system details.
- The answer does not ask students to share passwords, MFA codes, security answers, or other secrets.

## Rendered Test Coverage Review

Current rendered response tests already cover:

- Generic help and login disambiguation, including `I can’t log in` and `I need help`.
- Student email troubleshooting via `Student email not working`.
- MFA verification-code trouble via `I am not getting my verification code`.
- Lost phone MFA recovery via `I lost my phone and can't do MFA`.
- OneDrive web-access wording via `Can I use OneDrive with my school account?`.
- OBL location via `Where is OBL located?`.
- Zoom SSO variants, including `Zoom asks for SSO`.
- Several Wi-Fi, printing, classroom, and Zoom troubleshooting cases.

Coverage gaps to consider adding later:

- Add a rendered-response case for exact wording: `My student email is not working`.
- Add a rendered-response case for exact wording: `I got a new phone and can't approve MFA`.
- Add a rendered-response case for `Where is the Hub?` to protect Hub location/contact/hours and prevent OBL confusion.
- Add rendered-response cases for `Can I use Adobe?` and `Where can I use SolidWorks?` to protect verified software-access limits and locations.
- Add or confirm a rendered-response case for `How do I print on campus?`; routing/retrieval cover printing, but a student-facing rendered output check would better protect public wording.
- Consider adding negative assertions that public responses never include internal printer server paths, Entra admin details, or unverified Microsoft 365 desktop entitlement claims.

Do not add these tests in the same pass unless the output review finds a specific regression that needs protection.
