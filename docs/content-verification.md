# Content Verification Audit

Practical knowledge-base verification audit for the CCA IT Support Assistant.

Last updated: 2026-04-27

## Method

- Reviewed every public KB article under `content/public/`.
- Compared high-risk factual claims against public CCA sources when available.
- Used these source-status labels:
  - `verified_public_source`
  - `likely_but_needs_human_verification`
  - `unsupported_claim`
  - `inconsistent_with_other_kb_content`
  - `needs_source`
- Did not assume KB correctness just because automated tests passed.
- Did not change retrieval logic, classifier behavior, or UI behavior as part of this audit.

## Public Sources Used

- Community College of Aurora contact page: `https://ccaurora.edu/contact/`
  - Verified by the page content and consistent with the known public contact details already provided for:
    - IT Helpdesk phone `303-360-4900`
    - IT Helpdesk hours `Monday–Friday, 8 a.m.–5 p.m.`
    - after-hours/weekend support `1-888-800-9198`
    - helpdesk email `helpdesktickets.cca@ccaurora.edu`
- Educational Technology LibGuide home: `https://cccs.libguides.com/CCAEdTech`
- Student Email page: `https://cccs.libguides.com/c.php?g=1401795&p=11251646`
- Student Laptops & Calculators page: `https://cccs.libguides.com/c.php?g=1401795&p=10508349`
- Classroom Technology page: `https://cccs.libguides.com/c.php?g=1401795&p=10739286`
- Office 365 page: `https://cccs.libguides.com/c.php?g=1401795&p=10619586`
- Windows 11 page: `https://cccs.libguides.com/c.php?g=1401795&p=10445717`
- CCA catalog / facilities pages surfaced publicly for CentreTech building references.
- CCA IT Support flyer / campus support handout
  - Verification date: 2026-04-27
  - Verified:
    - Student Wi-Fi SSID `CCA-Students`
    - `CCA-Students` is an open network that requires no password
    - users must agree to the consent page and continue to the internet
    - IT Helpdesk phone `303-360-4900`
    - IT Helpdesk hours `Monday through Friday, 8 a.m.–5 p.m.`
    - after-hours 24/7 support `1-888-800-9198`
    - support ticket email `Helpdesktickets.cca@ccaurora.edu`

## Verification Table

| File | Claim | Current KB value | Risk | Source status | Recommended action |
|---|---|---|---|---|---|
| `cca-tech-help.txt` | Standard IT Helpdesk block | `303-360-4900`, `1-888-800-9198`, `HelpdeskTickets.CCA@ccaurora.edu`, `Mon–Fri 8 a.m.–5 p.m.` | low | `verified_public_source` | Keep standardized block. Verified 2026-04-27 from CCA contact page and CCA IT Support flyer / campus support handout. |
| `cca-tech-help.txt` | Hub Front Desk handles headphones / calculators / general student tech help | General Hub-front-desk routing | medium | `needs_source` | Verify Hub service ownership with Student Success or Hub staff. |
| `classroom-technology.txt` | Classroom tech escalation email | `HelpdeskTickets.CCA@ccaurora.edu` | low | `verified_public_source` | Keep. |
| `classroom-technology.txt` | Classroom display / projector / audio issues should route to IT Helpdesk | IT owns classroom AV escalation | medium | `likely_but_needs_human_verification` | Confirm ownership and after-hours expectations with Educational Technology / IT. |
| `contact-it.txt` | Standard IT Helpdesk block | `303-360-4900`, `1-888-800-9198`, `HelpdeskTickets.CCA@ccaurora.edu`, `Mon–Fri 8 a.m.–5 p.m.` | low | `verified_public_source` | Keep as canonical escalation reference. Verified 2026-04-27 from CCA contact page and CCA IT Support flyer / campus support handout. |
| `d2l-troubleshooting.txt` | LMS naming | `D2L (Brightspace)` | low | `likely_but_needs_human_verification` | Keep wording; confirm if CCA wants student-facing copy to say `D2L`, `Brightspace`, or both. |
| `d2l-troubleshooting.txt` | Support ownership split | IT for sign-in / technical issues, instructor for missing course or assignment availability | medium | `likely_but_needs_human_verification` | Confirm with Academic Affairs / OBL that this escalation split is official. |
| `d2l.txt` | D2L access via student account credentials | Students sign in with CCA student credentials | medium | `likely_but_needs_human_verification` | Confirm exact entry path and whether CCA still routes through MyCCA or another SSO path. |
| `it-resources.txt` | Hub campus coverage | Hub available at both CentreTech and Lowry campuses | medium | `needs_source` | Verify against current campus services page. |
| `it-resources.txt` | Hub location and phone | `Classroom Building 107`, `303-360-4736` | high | `needs_source` | Verify with current CCA campus services source before relying on it in student-facing answers. |
| `mfa-account-security.txt` | MFA requirement scope | MFA may affect MyCCA, student email, and other CCA services | high | `likely_but_needs_human_verification` | Student email MFA is supported publicly; verify whether MyCCA itself also enforces MFA. |
| `mfa-account-security.txt` | Verification-code / prompt / changed-phone support path | IT Helpdesk owns blocked MFA access issues | medium | `likely_but_needs_human_verification` | Confirm with IT whether MFA account recovery always routes to the Helpdesk. |
| `online-blended-learning.txt` | OBL contact email | `onlinelearning.cca@ccaurora.edu` | medium | `verified_public_source` | Keep; public source also shows mixed-case `OnlineLearning.CCA@ccaurora.edu`. |
| `online-blended-learning.txt` | OBL location | `Fine Arts Building, Room F103` | high | `inconsistent_with_other_kb_content` | Do not auto-correct. Human verification required: public catalog pages place Online Learning in the Classroom Building, while other public pages reference Fine Arts rooms. |
| `online-blended-learning.txt` | OBL support ownership | OBL handles online course design / instructional support, IT handles technical login/system issues | medium | `likely_but_needs_human_verification` | Confirm with OBL and IT. |
| `password-reset.txt` | MyCCA / campus computer password relationship | same password for myCCA and CCA computers | medium | `likely_but_needs_human_verification` | Confirm current identity model with IT. |
| `password-reset.txt` | Password reset path | reset through `ccaurora.edu` / MyCCA login flow | medium | `needs_source` | Verify exact public reset flow and whether self-service reset instructions should be more specific. |
| `printing.txt` | Printing help location | Printing help available at the Hub front desk | medium | `likely_but_needs_human_verification` | Confirm current print-support ownership. |
| `printing.txt` | Student-owned devices must use campus Wi-Fi before printing | Printing from own device may depend on campus Wi-Fi | medium | `likely_but_needs_human_verification` | Verify with printing instructions. |
| `printing.txt` | Wi-Fi network spelling in public source | KB printing guidance implies student Wi-Fi; public LibGuide home snippet says `CCAStudents wifi` | high | `inconsistent_with_other_kb_content` | Keep flagged until Wi-Fi naming is confirmed campus-wide. |
| `student-email-office365.txt` | Microsoft 365 access with school account | Students can sign in with CCA school account to use Outlook, Teams, OneDrive, Office Online | high | `likely_but_needs_human_verification` | Likely true, but verify current licensing / access policy with Microsoft 365 admin. |
| `student-email-office365.txt` | OneDrive usage | Students can store, sync, and share school files in OneDrive | medium | `likely_but_needs_human_verification` | Verify whether OneDrive is enabled for all student accounts. |
| `student-email-troubleshooting.txt` | Duo / MFA as a primary student email sign-in dependency | Main steps require completed Duo/MFA enrollment and prompt approval | high | `verified_public_source` | Keep. Student email public page says first access prompts MFA setup. |
| `student-email-troubleshooting.txt` | Outlook web as a fallback | Try Outlook on the web to distinguish account vs app issue | medium | `likely_but_needs_human_verification` | Keep; validate with IT if Outlook Web is the preferred fallback path. |
| `student-email.txt` | Student email domain | `@student.cccs.edu` | low | `verified_public_source` | Keep. |
| `student-email.txt` | Initial MyCCA password format | `StudentMMDDYYYY` default or updated password | high | `verified_public_source` | Keep, but review periodically because default-password rules are sensitive. |
| `student-email.txt` | First student email access triggers MFA setup | First login prompts MFA; phone number method recommended | medium | `verified_public_source` | Keep. |
| `student-laptops-calculators.txt` | Semester laptop loan location | `Student Centre, Room S101, CentreTech Campus` | low | `verified_public_source` | Keep. |
| `student-laptops-calculators.txt` | Semester laptop loan requirements | bring student ID and current course schedule | low | `verified_public_source` | Keep. |
| `student-laptops-calculators.txt` | Calculator checkout | Hub front desk at CentreTech; provide S# | low | `verified_public_source` | Keep. |
| `wifi-troubleshooting.txt` | Student Wi-Fi network name | `CCA-Students` | low | `verified_public_source` | Keep. Verified 2026-04-27 from CCA IT Support flyer / campus support handout. |
| `wifi-troubleshooting.txt` | Open/no-password Wi-Fi claim | `CCA-Students is an open network and does not require a password` | low | `verified_public_source` | Keep. Verified 2026-04-27 from CCA IT Support flyer / campus support handout. |
| `wifi-troubleshooting.txt` | Captive portal / splash page behavior | open browser to trigger splash page / captive portal / consent page | low | `verified_public_source` | Keep. Verified 2026-04-27 from CCA IT Support flyer / campus support handout. |
| `wifi-troubleshooting.txt` | IT escalation block | Standard Helpdesk block | low | `verified_public_source` | Keep. Verified 2026-04-27 from CCA contact page and CCA IT Support flyer / campus support handout. |
| `windows-11.txt` | Windows 11 mapped-drive recovery path | `\\\\CCADFS01.ccc.ccofc.edu\\gpdeploy$\\SelfService` and `MapDrives` | medium | `verified_public_source` | Keep only if still active; verify periodically because infrastructure details can change. |
| `windows-11.txt` | Remote access requirement | VPN required before mapped-drive repair when remote | medium | `verified_public_source` | Keep, but mark as time-sensitive in future review. |
| `windows-11.txt` | Upgrade timeline and deadline | upgrade notice beginning `Friday, September 19th`; Windows 10 end of support `October 14th, 2025` | high | `verified_public_source` | Treat as stale/time-bound. Remove or archive dated rollout language if this article stays in production. |
| `yuja-panorama.txt` | YuJa Panorama supports course videos and accessibility | YuJa used for media/accessibility in CCA courses | medium | `likely_but_needs_human_verification` | Keep; confirm ownership and student support path with OBL. |
| `yuja-panorama.txt` | Accessibility support contact path | Follow course guidance first; IT Helpdesk if issue continues | medium | `likely_but_needs_human_verification` | Confirm whether OBL should be named before IT for accessibility/course-media issues. |
| `zoom-support.txt` | Zoom usage context | Zoom is used for online / blended / remote class meetings | low | `likely_but_needs_human_verification` | Keep; low factual risk. |
| `zoom-support.txt` | Support ownership split | OBL for course-related Zoom support; IT for login/device/technical issues | medium | `likely_but_needs_human_verification` | Confirm ownership boundary with OBL and IT. |

## High-Risk Claims Requiring Human Verification

- `online-blended-learning.txt`
  - OBL location `Fine Arts Building, Room F103`
  - Public sources conflict with catalog/facilities references that place Online Learning in the Classroom Building
- `student-email-office365.txt`
  - Whether all students currently have OneDrive / Teams / Office Online access with the same school account path described in the KB
- `windows-11.txt`
  - Whether dated upgrade instructions should remain published
- `it-resources.txt`
  - Hub location / phone / Lowry availability

## TODOs For Human Verification

- TODO: Confirm whether MyCCA itself now requires MFA, or only downstream Microsoft 365/student-email sign-ins do.
- TODO: Confirm the current OBL physical location and whether `Fine Arts Building, Room F103` is still correct.
- TODO: Confirm whether `onlinelearning.cca@ccaurora.edu` remains the public-facing OBL support address for students/faculty.
- TODO: Confirm current Microsoft 365 / OneDrive / Teams entitlements for student accounts.
- TODO: Confirm Hub locations, phone numbers, and which services are offered at CentreTech vs Lowry.
- TODO: Confirm whether D2L student support should explicitly reference `D2L`, `Brightspace`, `MyCourses`, or a preferred combination in student-facing copy.
- TODO: Review `windows-11.txt` for stale rollout dates and infrastructure details before long-term production use.
