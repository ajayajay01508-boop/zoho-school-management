# Zoho deployment guide

This guide installs the supplied source in a dedicated evaluation organization. It records work still required; it does not assert that these steps have been executed. Do not use a school production tenant for the initial installation.

## 1 Prepare the evaluation organization

Use a Zoho account with CRM and Creator access. The assignment allows a Zoho One trial. Verify the plan supports 18 custom CRM modules, functions, workflows, a Creator portal, pages, connections and schedules. Custom-module creation via the documented API requires Enterprise or above. Module creation consumes 500 API credits per module; eighteen modules therefore consume 9000 credits before field creation. Check the trial quota first or create modules through the UI.

Set the organization timezone to Asia/Kolkata and its currency to INR. Record the actual data centre and account owner. The included Deluge endpoints default to India; select the account's actual API domain with:

```sh
python deploy/set_region.py www.zohoapis.in
```

Do not infer an account's data centre from the student's location. Confirm the domain from the signed-in Zoho account and OAuth response.

## 2 Provision CRM metadata

Create a dedicated administrator profile for the evaluation if needed. Obtain its actual profile ID using CRM settings or GET /crm/v8/settings/profiles. Use an OAuth token with CRM module/field metadata read and create permissions. Store the token only in local environment variables through a secure local mechanism; do not put it in chat, this source tree, an email or a screenshot.

Required environment variable names:

| Variable | Meaning |
|---|---|
| ZOHO_ACCESS_TOKEN | Short-lived OAuth access token |
| ZOHO_API_DOMAIN | The account's exact HTTPS API origin |
| ZOHO_ADMIN_PROFILE_ID | Authorized evaluation administrator profile |

Run `python deploy/provision.py` to inspect the offline plan. Run `python deploy/provision.py --apply` only against the intended evaluation org. It creates missing custom modules restricted to the provided profile, then fields one at a time. It stops on a failed response, mismatched field API name or incompatible existing type rather than deleting or overwriting metadata. Re-running resumes missing metadata.

After creation, verify all actual API names match schema/crm_schema.json. In Students, verify that the generated auto-number display field's API name is `Name` and its label is Student ID. If Zoho assigns another name, align the account or source before continuing. Check all unique fields and lookup targets. Mandatory metadata in the schema is a setup instruction: the script does not set layout-required flags. Configure those flags in the CRM layout editor. Leave Guardian Email Key optional on initial creation so normalization can populate it; require a nonempty key before identity verification.

Add the remaining admission options to the custom Admission Status field. Set webform enquiries to New. Do not use standard Lead conversion for this model. Configure Lead views for open enquiries, approved but not processed, rejected enquiries and nonempty Admission Error.

## 3 Configure connections and staff access

Create `sms_crm` for CRM Deluge operations. It needs access to the specific school modules plus Leads, and COQL READ. The initial demo should be administrator-only. Never publish the internal query or insert helpers as REST functions. Do not enable API-key access. Expose only the operation functions that the widget needs through authenticated OAuth execution.

Create `crm_parent_read` in Creator as an administrator-authorized, server-side connection. Grant CRM READ only for Guardians, Student Guardians, Students, Enrollments, Class Sections, Academic Years, Attendance, Results, Exam Papers, Examinations, Fee Invoices and Payments, plus COQL READ. Add only metadata/related modules actually required by the queries. Do not enable credentials of the logged-in parent. The parent does not have a CRM account and must never receive the connection token.

Create `crm_scheduler` separately for authenticated execution of the scheduled CRM functions. Do not grant Creator portal users access to this connection or schedule configuration.

Before adding non-admin staff, configure least-privilege CRM profiles and prove them with the negative tests in LIVE_ACCEPTANCE.md. Teachers need scoped academic reads and attendance/result operation access; admission staff manage Leads; finance staff manage invoices and payments; parents have Creator page access only. A hidden button is not authorization. A function with an org-owned connection can exceed a caller's record permissions unless execution access is properly restricted. Until this is verified, keep every operation and widget restricted to the evaluation administrator. Do not grant regular staff broad API, import, delete, mass update or direct transaction-edit access.

## 4 Install and compile Deluge

Create functions using their exact names, return types and argument mappings. If Zoho's editor generates the signature, paste the body into that signature rather than nesting a second declaration. Compile helpers first, then operations. `04_sms_record_attendance` depends on `05_sms_refresh_attendance`; `07_sms_record_payment` and `11_sms_create_invoice` depend on `08_sms_refresh_fees`. Install 01, 02, 05, 08 before the functions that call them.

| File | Association |
|---|---|
| 01 sms query | Internal standalone helper; no public REST exposure |
| 02 sms insert once | Internal standalone helper; no public REST exposure |
| 03 sms confirm admission | Approved Lead processing and manual retry |
| 04 sms record attendance | Authenticated staff widget operation |
| 05 sms refresh attendance | Internal summary recalculation |
| 06 sms record result | Authenticated staff widget operation |
| 07 sms record payment | Authenticated finance operation |
| 08 sms refresh fees | Internal summary recalculation |
| 09 sms overdue batch | Administrator schedule only |
| 10 sms promote | Serialized administrator operation |
| 11 sms create invoice | Authenticated finance operation |
| 12 sms normalize guardian | Guardians create and Email change workflow |
| 13 sms admission workflow | Leads on Admission Status becoming Approved |
| 14 sms reconcile batch | Administrator reconciliation job |

Attach the guardian workflow on create and when Email changes. It computes SHA256(trim(lowercase(Email))) and resets Identity Verified and Portal Enabled to false if the email key changes. Verify identity and mailbox ownership separately before enabling them. The admission workflow invokes the operation and records a safe error code on the Lead if any stage fails. Configure its trigger only for the transition to Approved, not every edit.

Compile and execute every function in Zoho with synthetic records. Confirm the actual shape of COQL lookup/aggregate responses, the duplicate-create response ID, the Creator portal email LIST return, and function execution response output. Local Python tests do not verify these platform bindings. Fix any compiler or runtime differences, then rerun the live acceptance cases.

## 5 Configure validation and editing controls

The staff operation functions validate before insertion. Database unique fields are essential: they arbitrate simultaneous requests and cannot be replaced by a search-before-create pattern. Mark all Record Keys, Active Keys and Payment References as unique where specified, and required on their transaction layouts. Keep IDs, computed summaries, marks snapshots and keys read-only for normal staff.

Configure CRM validation rules for direct administrator entry and imports as applicable:

| Module | Rule |
|---|---|
| Academic Years | Start Date must not exceed End Date; one chosen current year |
| Enrollments | Valid dates within section academic year; current Active Key equals Student ID; archived key includes enrollment ID |
| School Days | Record Key equals section ID plus ISO school date; avoid deleting referenced days |
| Teaching Assignments | Unique section and subject allocation key; active teacher |
| Exam Papers | Max Marks greater than zero; Pass Marks between zero and maximum; examination and teaching assignment section match |
| Results | Marks nonnegative and not greater than snapshot maximum; absence requires zero; published exams locked |
| Fee Invoices | Total Fee nonnegative; no arbitrary edits after payments without an audited correction |
| Payments | Amount greater than zero; nonfuture date; Posted or Void only; Void requires reason; reference, invoice and amount immutable |
| Student Guardians | Access requires a verified Guardian and a deliberate administrator grant |

Cross-record checks remain in the supplied operation functions. Native UI validation, field protection, API permissions and imports must be configured and tested separately. The provisioning script does not install those controls. Do not claim direct CRM edits are protected until the tests prove it. The API insert helper requests validation-rule execution, but an unauthorized alternate write path must also be denied at the profile level.

## 6 Install the staff widget

Create an internally hosted CRM widget using staff-widget.zip. Set its index page to `/index.html` if the uploaded ZIP contains files at its root. It contains the same app files as staff-widget/app. Attach it to a web tab or custom record button. Record-button context prefills enrollment, invoice or lead ID. Authorize only the intended staff profiles and enable OAuth execution for the named operation functions. Verify the exact function argument mapping in Zoho. No JavaScript credential is required.

## 7 Build the Creator parent app

Create an app named School Parent Portal. Add the `crm_query`, `html_escape` and `parent_data` functions from deluge/creator using the exact return types and names. Create a Page with link name `Parent_Home`, add string parameters `sid`, `eid`, `category` and `p`, and place 04_parent_home.html in an HTML snippet. Set category default to attendance and p default to 0. Keep page access authenticated and share only this page with the parent portal permission set.

Disable public page access and public self-registration. Do not expose a generic Custom API accepting queries or parent email. Do not share administrative forms or CRM credentials. Invite controlled parent test accounts only after you have explicitly approved sharing the demo. Use two different parent accounts to prove access isolation, not just the creator-owner preview. Owner preview does not prove portal session identity.

Create verified Guardian records and Student Guardian grants. Test the entire hierarchy: parent A with two children, parent B with another child, different enrollment IDs, disabled grants, disabled guardian and changed email. Reopening an old page URL must reauthorize against current CRM grants.

## 8 Schedule work queues and summaries

For 05_overdue_scheduler create an internal Creator form `Job_State` with fields Name (single line, no duplicates), Run_Date (date), Cursor_ID (single line), Is_Complete (checkbox) and Last_Error (single line). Create one record Name=overdue, Cursor ID=0, Is Complete=false. Do not share it with parents. Install the function and attach an available scheduled workflow in the actual plan. It processes one batch per invocation and persists the cursor. Manually invoke it until complete for the demo; for a larger school set a supported cadence that finishes the workload daily. Avoid overlapping executions. An error leaves the failed work available for retry.

For whole-ledger repair run sms_reconcile_batch starting after_id=0 and entity=Fee_Invoices, then Enrollments. Continue using next_after until more_records=false; persist a separate cursor per job when attaching a scheduler. Run after voids, calendar changes and bulk administrative corrections. This reconciliation scheduler binding remains an account configuration task; the supplied automatic Creator scheduler currently binds the overdue job only.

## 9 Configure the admission webform

In CRM Setup, create a Leads Webform named School Admission Enquiry. Include Last Name (guardian name), Email, Phone, Child Name, Child DOB and Parent Consent. Keep Requested Section and Verified Guardian as staff-controlled fields; staff assign a section and Enrollment Start before approval. Use a hidden New Admission Status or its default, Lead Source=Webform, an assigned admission owner and an acknowledgement/thank-you page. Do not expose Admitted Student, identity flags, payment fields or privileged workflow status fields.

Enable the product's available spam protection and domain restrictions. Export the genuine form embed snippet, including its Zoho-generated routing fields. Assemble a landing page using:

```sh
python webform/assemble.py path/to/exported-form.html admission.html
```

Host the assembled form at an authorized HTTPS location or use Zoho's supported published form facility. Do not invent hidden form tokens or a return URL. Submit one synthetic enquiry through the actual public page, confirm it reaches Leads exactly once, and capture its real URL for the submission. The package does not contain a working form because no organization-specific export exists yet.

## 10 Reports and final acceptance

Create the reports in REPORTS.md and add their charts to a School Overview dashboard. Enter the synthetic demo scenario, run all cases in LIVE_ACCEPTANCE.md, save redacted screenshots and actual URLs, and update verification-status.json only from observed results. Record a short demo if desired. Complete the handover's access section before sending any submission. The recipient address is sagar@it-guy.tech; this package does not send email.

## Source references

Official references used to prepare the implementation:

- [CRM custom module API](https://www.zoho.com/crm/developer/docs/api/v8/create-custom-module-api.html)
- [CRM custom fields API](https://www.zoho.com/crm/developer/docs/api/v8/create-custom-field.html)
- [CRM record creation and validation execution](https://www.zoho.com/crm/developer/docs/api/v8/insert-records.html)
- [CRM COQL](https://www.zoho.com/crm/developer/docs/api/v8/COQL-Overview.html)
- [Creator portal email task](https://www.zoho.com/deluge/help/misc-statements/get-portal-user-emailid.html)
- [Creator HTML snippets](https://help.zoho.com/portal/en/kb/creator/developer-guide/pages/snippets/articles/understand-html-snippets)
- [CRM widget creation](https://www.zoho.com/crm/developer/docs/widgets/create-widget.html)
- [CRM widget SDK function execution](https://help.zwidgets.com/help/v1.0.1/ZOHO.CRM.FUNCTIONS.html)
- [Zoho SDK releases](https://github.com/zoho/embeddedApp-js-sdk/releases)
