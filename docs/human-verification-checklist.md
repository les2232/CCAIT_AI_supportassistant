# Human Verification Checklist

Concise handoff checklist for pilot claims that still need a human source of truth before public KB wording should become more specific.

Status options: `pending`, `verified`, `needs_softening`, `do_not_publish`.

| Item | Claim to verify | Why it matters | Suggested owner/team | Status | Notes |
|---|---|---|---|---|---|
| Current OBL physical location | The current in-person location for Online and Blended Learning, if any, and whether a room number should appear in student-facing guidance. | Public sources have conflicted; publishing the wrong room sends students/faculty to the wrong place. | Online and Blended Learning; Educational Technology; campus facilities contact if needed | `pending` |  |
| Microsoft 365 student entitlements | Which Microsoft 365 services are available to student accounts, including Outlook, OneDrive, Teams, and Office Online. | The assistant should not imply all students have identical licensing, storage, sync, sharing, or web-app access. | IT Microsoft 365 administrator; Identity/access team | `pending` |  |
| Exact services requiring MFA | Which current CCA student-facing services require MFA, including whether MyCCA itself requires MFA. | MFA scope affects routing and public guidance; overclaiming can misdirect students with login issues. | Identity/access team; IT Helpdesk lead; Microsoft 365 administrator | `pending` |  |
| MFA changed-phone/account-recovery ownership | Whether changed-phone, lost-device, missing prompt, and failed verification cases always route to the CCA IT Helpdesk, 24x7 Help Desk, or another process. | Students blocked by MFA need the correct recovery path, and public guidance should not invent an escalation procedure. | IT Helpdesk lead; Identity/access team | `pending` |  |
| Hub services, locations, hours, and campus availability | Current Hub services, where the Hub operates, campus coverage, phone numbers, and hours. | Hub guidance appears in multiple public support paths and must reflect actual service availability. | Hub leadership; Student Success; campus services owner | `pending` |  |
| Hub laptop availability | Whether laptops are currently available for use inside the Hub, at which campus/location, and under what limits. | The public KB references Hub laptop availability; incorrect availability creates bad in-person referrals. | Hub leadership; Student Success; Educational Technology if applicable | `pending` |  |
| Adobe Creative Cloud on iMacs | Whether Hub iMac desktops currently have Adobe Creative Cloud installed and available for student coursework. | The public KB names a specific software/location combination that may change over time. | Hub leadership; lab/desktop support; software licensing owner | `pending` |  |
| SolidWorks on one desktop PC | Whether one Hub desktop PC currently has SolidWorks installed and available for student coursework. | The public KB names a specific software/location combination that may change over time. | Hub leadership; lab/desktop support; software licensing owner | `pending` |  |

When an item is verified, update `docs/content-verification.md` before strengthening any public KB wording.
