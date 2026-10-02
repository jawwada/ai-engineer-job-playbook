# Indeed playbook: prefill only, never submit

The agent scouts and prefills Indeed applications but never submits them, in any mode. The user
clicks the final submit.

## Flows

- **Apply now** or **Easily apply** (hosted by Indeed, usually on smartapply.indeed.com): prefill as
  below and stop before the final submit.
- **Apply on company site**: the application happens on the employer's ATS. Record that URL as
  `apply_url` and follow ats.md (submission by mode; if an account is required, stop).

## Prefill (Indeed-hosted)

1. Open `https://www.indeed.com/viewjob?jk=<key>` and click **Apply now**. At a sign-in page, a
   verification code or a "verify you are human" check, stop and hand over.
2. **Contact information**: name, email, city and state, and phone from `identity`. Do not edit the
   saved Indeed profile.
3. **Resume**: choose to upload a file and upload the tailored PDF with the upload tool. If the file
   input is hidden, inject `linkedin-helper.js` and run `jobHelper.exposeFile()`. Do not pick the
   Indeed-built resume.
4. **Employer questions**: answer from answers.yaml, answers.md or skills_years only. Leave unknown
   ones empty and list them for the user.
5. **Relevant experience** (some forms): the job title and company of the most recent role in the
   master resume.
6. **Review your application**: STOP. Do not click "Submit your application".

## Handover

- `.venv/bin/python scripts/tracker.py update <id> --status ready --notes "Indeed prefilled; user submits"`
- Tell the user which tab it is, the answers entered, and anything left empty. When they confirm
  they submitted it, record `submitted` with "submitted by user on Indeed".
- Leave Indeed's optional prompts (job alerts, profile visibility, saving the resume) for the user;
  do not accept or decline them.
