# Zoho School Management System

**Status: work in progress. Local Python checks pass; Deluge compilation and live Zoho deployment remain unverified.**

A school operations implementation for Zoho CRM and Zoho Creator, covering admissions, attendance, results, fee tracking and parent access. This repository contains deployment source and an executable Python reference model. It does not yet provide a verified live CRM, Creator portal or admission webform.

## What is included

- CRM metadata specification: 18 custom modules, 98 custom fields including Leads extensions, and relationship dictionary.
- Fourteen CRM Deluge source files for admissions, attendance, examinations, fees, promotions, guardian identity, and reconciliation.
- Creator source for authenticated parent access, paginated school records, HTML escaping and the overdue job.
- Embedded CRM staff widget for entering operations through the Deluge functions.
- CRM metadata provisioning CLI with an offline default, region configuration, and checked API responses.
- Webform assembly utility that requires a genuine Zoho-generated webform export.
- Executable Python business-rule reference and 42 local checks. These are not Deluge or live Zoho tests.
- Deployment instructions, report definitions, demo fixtures, live acceptance checklist, and a conditional submission draft.

## Quick local verification

Python 3.10 or newer; the reference and tests use the standard library only.

```sh
python deploy/run_checks.py
python -m reference.domain
python deploy/provision.py
```

The last command prints an offline plan and changes nothing outside this folder. To provision an authorized Zoho evaluation organization, follow `docs/DEPLOYMENT.md`. The CLI provisions metadata only; permissions, layouts, functions, workflows, Creator, reports, portal accounts and webform activation still require Zoho configuration and verification.

## Start here

1. `docs/ARCHITECTURE.md` — data model, integration decisions and extra feature.
2. `docs/DEPLOYMENT.md` — installation and account-dependent configuration.
3. `docs/LIVE_ACCEPTANCE.md` — evidence required before claiming completion.
4. `docs/REPORTS.md` — CRM management reports and dashboard metrics.
5. `fixtures/DEMO_DATA.md` — synthetic demonstration scenario and expected outputs.
6. `docs/SUBMISSION_DRAFT.md` — use only after all live requirements pass.

`evidence/local-test-results.txt` and `evidence/verification-status.json` distinguish what was tested from what remains unverified. Do not rename local reference output as Zoho evidence. Deluge source has not been compiled by Zoho; API bindings, runtime return shapes, permissions and plan entitlements must be validated in the target account.

## Credentials and data

No passwords, OAuth tokens, organization routing IDs, actual child records or real parent addresses are included. Synthetic addresses use example.test and cannot receive portal invitations. Use controlled test mailboxes for live access tests. Keep CRM and Creator private and do not place tokens in the widget or webform.
