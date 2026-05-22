# Content Verification Audit

Practical knowledge-base verification audit for the CCA IT Support Assistant.

Last updated: 2026-05-22

## Method

- Reviewed every public KB article under `content/public/`.
- Compared high-risk factual claims against public CCA sources when available.
- Used these source-status labels:
  - `verified_public_source`
  - `verified_human_source`
  - `partially_verified_human_source`
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
| `cca-tech-help.txt` | Hub help with headphones / calculators / general student tech help | Hub can help route general student technology support; CentreTech Hub location, phone, email, and hours are verified; headphone availability and exact checkout desk still need confirmation | medium | `partially_verified_human_source` | Public KB updated 2026-05-22 to say the Hub more generally and avoid overclaiming a specific front desk for unverified items. Hub contact/hours updated 2026-05-22 from human-verified current Hub page/screenshot. Verify headphone availability and exact calculator/headphone checkout ownership with Hub staff. |
| `classroom-technology.txt` | Classroom tech escalation email | `HelpdeskTickets.CCA@ccaurora.edu` | low | `verified_public_source` | Keep. |
| `classroom-technology.txt` | Classroom display / projector / audio issues should route to IT Helpdesk | IT owns classroom AV escalation | medium | `likely_but_needs_human_verification` | Confirm ownership and after-hours expectations with Educational Technology / IT. |
| `contact-it.txt` | Standard IT Helpdesk block | `303-360-4900`, `1-888-800-9198`, `HelpdeskTickets.CCA@ccaurora.edu`, `Mon–Fri 8 a.m.–5 p.m.` | low | `verified_public_source` | Keep as canonical escalation reference. Verified 2026-04-27 from CCA contact page and CCA IT Support flyer / campus support handout. |
| `d2l-troubleshooting.txt` | LMS naming | Student-facing copy prioritizes `D2L/Desire2Learn`; Brightspace remains in limited access/search wording where useful | low | `partially_verified_human_source` | Human-verified screenshot uses `Desire2Learn`. Public KB updated 2026-05-22 to use `D2L/Desire2Learn` for main guidance. Confirm separately if CCA wants Brightspace removed from student-facing copy. |
| `d2l-troubleshooting.txt` | Support ownership split | IT for sign-in / technical issues, instructor for missing course or assignment availability | medium | `likely_but_needs_human_verification` | Confirm with Academic Affairs / OBL that this escalation split is official. |
| `d2l.txt` | D2L access path | Students log in to MyCCA and click the Desire2Learn/D2L link to access D2L/Desire2Learn courses | medium | `verified_human_source` | Public KB updated 2026-05-22 from human-verified online-learning screenshot. Do not claim MyCCA itself requires MFA unless separately verified. |
| `d2l.txt` / `d2l-troubleshooting.txt` / `online-blended-learning.txt` | Online course readiness | Online courses require reliable internet; students should run the D2L/Desire2Learn system check at `https://cca.desire2learn.com/d2l/systemCheck`; students new to online classes should meet with a Pathways Advisor before enrolling | medium | `verified_human_source` | Public KB updated 2026-05-22. Keep IT/OBL technology support distinct from Pathways Advisor academic-preparation guidance. |
| `it-resources.txt` | Hub campus coverage | The CentreTech Hub is in the Classroom Building, Room 107; many Hub services can also be accessed online | medium | `verified_human_source` | Public KB updated 2026-05-22. This verifies the CentreTech Hub location and online-access note; it does not verify separate service-specific desk ownership. |
| `it-resources.txt` | Hub services, location, phone, and hours | Hub provides or connects students with tutoring, library support, research help, technology assistance, printing, and study spaces; phone is (303) 360-4736; email is TheHub.cca@ccaurora.edu; hours are Monday-Thursday 8 a.m. to 6 p.m., Friday 8 a.m. to 5 p.m., and Saturday 10 a.m. to 2 p.m. | high | `verified_human_source` | Public KB updated 2026-05-22 from human-verified current Hub page/screenshot. Use Hub contact info as a general Hub contact path, not as an IT Helpdesk replacement. |
| `mfa-account-security.txt` | MFA requirement scope | MFA is needed for student email access and may affect other services that ask for student-account verification; Microsoft Authenticator is optional | high | `partially_verified_human_source` | Public KB updated 2026-05-22. Exact MyCCA MFA requirement is not confirmed; do not claim MyCCA requires MFA unless separately verified. |
| `mfa-account-security.txt` | Verification-code / prompt / changed-phone support path | Students with a new phone, changed phone number, or changed verification device should contact CCA IT for help updating their verification method or phone number | medium | `verified_human_source` | Public KB updated 2026-05-22. Internal notes may mention Entra if needed; public KB should remain student-friendly and not over-explain Entra. |
| `online-blended-learning.txt` | OBL contact email | `onlinelearning.cca@ccaurora.edu` | medium | `verified_public_source` | Keep; public source also shows mixed-case `OnlineLearning.CCA@ccaurora.edu`. |
| `online-blended-learning.txt` | OBL location | OBL is in room F103 | medium | `verified_human_source` | Public KB updated 2026-05-22. Building name was not added because only room F103 was verified. |
| `online-blended-learning.txt` | OBL support ownership | OBL handles online course design / instructional support, IT handles technical login/system issues | medium | `likely_but_needs_human_verification` | Confirm with OBL and IT. |
| `password-reset.txt` | MyCCA / campus computer password relationship | same password for myCCA and CCA computers | medium | `likely_but_needs_human_verification` | Confirm current identity model with IT. |
| `password-reset.txt` | Password reset path | reset through `ccaurora.edu` / MyCCA login flow | medium | `needs_source` | Verify exact public reset flow and whether self-service reset instructions should be more specific. |
| `printing.txt` | Printing help location | Printing help can start with the Hub; CentreTech Hub location, phone, email, and hours are verified; exact front-desk ownership is not claimed in public KB | medium | `partially_verified_human_source` | Public KB updated 2026-05-22 based on verified Hub printing support category and current Hub contact/hours. Confirm exact print-support ownership before naming a specific desk. |
| `printing.txt` | Student-owned devices must use campus Wi-Fi before printing | Printing from own device may depend on campus Wi-Fi | medium | `likely_but_needs_human_verification` | Verify with printing instructions. |
| `printing.txt` | Wi-Fi network spelling in public source | KB printing guidance implies student Wi-Fi; public LibGuide home snippet says `CCAStudents wifi` | high | `inconsistent_with_other_kb_content` | Keep flagged until Wi-Fi naming is confirmed campus-wide. |
| `student-email-office365.txt` | Microsoft 365 access with school account | All students have access to Microsoft 365 products through the web, including Outlook, OneDrive, Teams, and Office Online | high | `verified_human_source` | Public KB updated 2026-05-22. Desktop app entitlement remains unverified and should not be claimed. |
| `student-email-office365.txt` | OneDrive usage | OneDrive web access is available through the CCA school account; desktop sync and detailed storage/sharing limits are not confirmed in public KB | medium | `partially_verified_human_source` | Public KB updated 2026-05-22. Keep desktop sync, storage quota, and sharing-limit claims out of public guidance unless verified. |
| `student-email-troubleshooting.txt` | MFA as a primary student email sign-in dependency | Student email troubleshooting now says required MFA or sign-in verification setup must be complete; Microsoft Authenticator is optional if another method is offered | high | `verified_human_source` | Public KB updated 2026-05-22. Keep student email MFA guidance, but do not claim a specific verification method is required. |
| `student-email-troubleshooting.txt` | Outlook web as a fallback | Try Outlook on the web to distinguish account vs app issue | medium | `likely_but_needs_human_verification` | Keep; validate with IT if Outlook Web is the preferred fallback path. |
| `student-email.txt` | Student email domain | `@student.cccs.edu` | low | `verified_public_source` | Keep. |
| `student-email.txt` | Initial MyCCA password format | `StudentMMDDYYYY` default or updated password | high | `verified_public_source` | Keep, but review periodically because default-password rules are sensitive. |
| `student-email.txt` | First student email access triggers MFA setup | MFA is needed for student email access; Microsoft Authenticator is optional; students should sign into email soon after registering for classes | medium | `verified_human_source` | Public KB updated 2026-05-22. Do not claim a specific MFA method is required. |
| `student-laptops-calculators.txt` | Semester laptop loan location | Loaner laptops can be found in the Student Center; public KB directs students to Student Success and keeps checkout details cautious | low | `partially_verified_human_source` | Public KB updated 2026-05-22. Exact checkout procedure, inventory, renewal options, and eligibility are not confirmed. |
| `student-laptops-calculators.txt` | Semester laptop loan requirements | Public KB says to bring student ID and current course schedule if requested | low | `partially_verified_human_source` | Public KB updated 2026-05-22. Keep exact checkout requirements cautious until confirmed. |
| `student-laptops-calculators.txt` | Calculator checkout | Hub front desk at CentreTech; provide S# | low | `verified_public_source` | Keep. |
| `student-laptops-calculators.txt` | Hub computer and desktop software availability | Loaner laptops can be found in the Student Center; CentreTech Hub location, phone, email, and hours are verified; Creative Cloud products are installed on CCA Macs with access limited to graphic design students or students whose class requires Adobe; SolidWorks is installed on Innovation Lab and CAST 132 computers | medium | `partially_verified_human_source` | Public KB updated 2026-05-22. Laptop checkout procedure, inventory, and eligibility remain unverified. |
| `wifi-troubleshooting.txt` | Student Wi-Fi network name | `CCA-Students` | low | `verified_public_source` | Keep. Verified 2026-04-27 from CCA IT Support flyer / campus support handout. |
| `wifi-troubleshooting.txt` | Open/no-password Wi-Fi claim | `CCA-Students is an open network and does not require a password` | low | `verified_public_source` | Keep. Verified 2026-04-27 from CCA IT Support flyer / campus support handout. |
| `wifi-troubleshooting.txt` | Captive portal / splash page behavior | open browser to trigger splash page / captive portal / consent page | low | `verified_public_source` | Keep. Verified 2026-04-27 from CCA IT Support flyer / campus support handout. |
| `wifi-troubleshooting.txt` | IT escalation block | Standard Helpdesk block | low | `verified_public_source` | Keep. Verified 2026-04-27 from CCA contact page and CCA IT Support flyer / campus support handout. |
| `windows-11.txt` | Windows 11 mapped-drive recovery process | Public article now avoids internal server path / script instructions and tells users what details to include when contacting IT | medium | `likely_but_needs_human_verification` | Confirm the supported mapped-drive recovery process, including whether any internal server path or self-service script should appear in public-facing guidance. |
| `windows-11.txt` | Remote mapped-drive recovery details | Public article asks users to tell IT whether they are on campus or remote instead of publishing VPN / internal path steps | medium | `likely_but_needs_human_verification` | Confirm whether remote mapped-drive recovery should include any public VPN guidance. |
| `windows-11.txt` | Upgrade timeline and deadline | Stale rollout / deadline wording removed; article now says Windows 10 reached Microsoft end of support on `October 14, 2025` | medium | `verified_public_source` | Addressed 2026-05-08. Keep current wording neutral unless CCA publishes new upgrade guidance. |
| `yuja-panorama.txt` | YuJa Panorama supports course videos and accessibility | YuJa used for media/accessibility in CCA courses | medium | `likely_but_needs_human_verification` | Keep; confirm ownership and student support path with OBL. |
| `yuja-panorama.txt` | Accessibility support contact path | Follow course guidance first; IT Helpdesk if issue continues | medium | `likely_but_needs_human_verification` | Confirm whether OBL should be named before IT for accessibility/course-media issues. |
| `zoom-support.txt` | Zoom usage context | Zoom is used for online / blended / remote class meetings | low | `likely_but_needs_human_verification` | Keep; low factual risk. |
| `zoom-support.txt` | Support ownership split | OBL for course-related Zoom support; IT for login/device/technical issues | medium | `likely_but_needs_human_verification` | Confirm ownership boundary with OBL and IT. |

## High-Risk Claims Requiring Human Verification

- `mfa-account-security.txt`
  - Email MFA and changed-phone/account-recovery routing were human-verified and public KB was updated 2026-05-22
  - Exact MyCCA MFA requirement remains unverified; do not claim MyCCA requires MFA
- `student-email-office365.txt`
  - Microsoft 365 web access for Outlook, OneDrive, Teams, and Office Online was human-verified and public KB was updated 2026-05-22
  - Desktop app entitlement, OneDrive desktop sync, storage quotas, and sharing limits remain unverified
- `windows-11.txt`
  - Stale Windows 11 rollout / deadline guidance was addressed 2026-05-08
  - Mapped-drive recovery remains verification-sensitive; do not publish internal server paths or self-service script steps unless explicitly approved for public guidance
- `it-resources.txt`
  - Hub CentreTech location, Classroom Building, Room 107, service categories, online-access note, phone, email, and hours were human-verified and public KB was updated 2026-05-22
  - Exact desk ownership for laptops, printing, headphones, and other service-specific checkout paths remains unverified
- `student-laptops-calculators.txt`
  - Adobe Creative Cloud on CCA Macs and SolidWorks in the Innovation Lab / CAST 132 were human-verified and public KB was updated 2026-05-22
  - Laptop checkout procedure, exact inventory, renewal options, and eligibility remain unverified
- `d2l.txt` / `d2l-troubleshooting.txt` / `online-blended-learning.txt`
  - D2L/Desire2Learn access through MyCCA, online-course reliable internet, the system check URL, and Pathways Advisor guidance for first-time online students were human-verified and public KB was updated 2026-05-22
  - Keep Pathways Advisor guidance separate from IT support; do not imply IT can advise whether online learning is academically appropriate

## TODOs For Human Verification

- TODO: Confirm whether MyCCA itself now requires MFA, or only downstream Microsoft 365/student-email sign-ins do.
- TODO: Confirm which current student-facing CCA services require MFA before restoring any app-by-app MFA scope list to public guidance.
- TODO: Confirm whether `onlinelearning.cca@ccaurora.edu` remains the public-facing OBL support address for students/faculty.
- TODO: Confirm Microsoft 365 desktop app entitlement, OneDrive desktop sync behavior, storage quotas, and sharing limits before adding those details to public guidance.
- TODO: Confirm exact Hub desk ownership for laptops, printing, headphones, and other service-specific checkout paths before adding those details to public guidance.
- TODO: Confirm laptop checkout procedure, exact inventory, renewal options, and eligibility before adding those details to public guidance.
- TODO: Confirm whether any remaining `Brightspace` or `MyCourses` wording should stay in student-facing copy now that `D2L/Desire2Learn` access wording has been verified.
- TODO: Confirm the supported mapped-drive recovery process for Windows 11, including whether any internal server path or self-service script should appear in public-facing guidance.

## Addressed Cleanup Notes

- 2026-05-08: Removed stale future-facing Windows 11 rollout / deadline guidance from `windows-11.txt` and replaced it with current neutral Windows 10 end-of-support wording.
- 2026-05-08: Softened `it-resources.txt` Hub guidance to avoid unverified public-facing service, campus availability, location, phone, and hours details.
- 2026-05-08: Softened `student-email-office365.txt` Microsoft 365 entitlement wording to avoid implying all students have the same Outlook, Teams, OneDrive, Office Online, storage, sync, or sharing access.
- 2026-05-12: Softened `online-blended-learning.txt` OBL location wording to avoid presenting an unverified room number as authoritative.
- 2026-05-22: Softened `mfa-account-security.txt` MFA scope wording to avoid implying specific MyCCA, Microsoft 365 app, Adobe, Webex, or other service MFA requirements without verification.
- 2026-05-22: Restored verified OBL room guidance as F103 without adding an unverified building name.
- 2026-05-22: Updated Microsoft 365 public guidance to say students have web access to Outlook, OneDrive, Teams, and Office Online while avoiding desktop app entitlement claims.
- 2026-05-22: Updated MFA public guidance to say MFA is needed for student email, Microsoft Authenticator is optional, changed-phone/device issues should contact CCA IT, and MyCCA MFA requirements remain unclaimed.
- 2026-05-22: Updated Hub public guidance with verified CentreTech location, service categories, and online access availability; Hub hours/contact were verified later and are recorded below.
- 2026-05-22: Updated student laptop/software guidance with cautious Student Center laptop language, verified Adobe access limits, and verified SolidWorks locations.
- 2026-05-22: Updated D2L/online-learning public guidance with verified MyCCA-to-Desire2Learn/D2L access path, system check URL, reliable-internet requirement, and Pathways Advisor recommendation for first-time online students.
- 2026-05-22: Updated Hub public guidance with verified Classroom Building, Room 107 location, phone, email, and hours from current Hub page/screenshot; kept service-specific desk ownership cautious.
