# School Management System handover

Prepared for Ajay S for The IT Guy Zoho Developer assignment.

## Current delivery status

Implementation source and local verification are prepared. The live Zoho CRM, Creator portal and admission webform are not deployed or verified. This is a source handover, not a completed live submission. Nothing has been emailed or submitted.

The available browser was rejected by Zoho Accounts on 27 September 2026 with an outdated-browser message. That prevents authenticated installation and runtime checks in this session.

## What the source covers

CRM data model with 18 custom modules and 98 custom fields; admissions and unique student IDs; annual enrollment history; class, subject and teacher relationships; validated daily attendance; examination results; fee invoices and installment payments; authenticated parent retrieval; a staff-entry widget; and an overdue-fee work queue.

CRM remains the primary data store. The Creator parent page checks the logged-in portal identity and live parent–student relationship before every record request. It reads CRM data without maintaining a second editable student database.

The extra feature creates one overdue follow-up item per invoice and review date. It calculates current balance from posted payments, ignores settled invoices and persists a batch cursor for recovery.

## Verification

42 local Python reference and package checks passed. Staff widget JavaScript passed a syntax check. The local tests exercise duplicate requests, concurrent payment retries, attendance dates, parent isolation, enrollment history, examination marks and fee calculations. They do not execute or compile Deluge and do not validate Zoho permissions or integration behavior.

## Finish and submit

Follow docs/DEPLOYMENT.md in the authorized Zoho evaluation account. Compile and run the Deluge code, configure staff permissions and Creator portal access, create the actual webform, build reports and complete docs/LIVE_ACCEPTANCE.md. Record the three real reviewer URLs and observed evidence. Only then fill docs/SUBMISSION_DRAFT.md and send the final verified assignment.

Start with README.md. Field details, architecture, synthetic demo inputs, report definitions and local test evidence are included. No credentials or real student data are packaged.
