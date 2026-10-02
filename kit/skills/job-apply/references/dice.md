# Dice playbook

Start: `https://www.dice.com/job-detail/<uuid>` in a new tab. The user is signed in to Dice. At a
sign-in page or a bot check, stop and hand over.

## Which flow

- **Easy apply** or **Apply** that opens a Dice dialog or wizard: follow the steps below.
- **Apply on company site**, or a redirect to an external page: record that URL as `apply_url` and
  use ats.md (if an account is required, stop).
- The page already shows **Applied**: update the row and stop.

## Dice apply wizard (labels vary)

1. **Resume**: Dice offers the resume stored on the profile. Choose to upload or replace it for this
   application and upload the tailored PDF with the upload tool. If the file input is hidden, inject
   `linkedin-helper.js` and run `jobHelper.exposeFile()` (it works on any page with a file input).
   If Dice says the upload replaces the resume saved on the profile, ask the user once per session
   whether that is acceptable, and note the answer in the tracker.
2. **Cover letter**: optional. Upload the tailored cover letter PDF only if the posting asks for one.
3. **Screener questions** (some employers): answer from answers.yaml, answers.md or skills_years only.
4. **Review**: check that the tailored file name is attached. Review mode stops here.
5. **Submit**: in auto mode, or after the user says "submit <id>".

## After submitting

- Expect a confirmation such as "Application submitted". Reload the job page: it should show
  **Applied**. Record `submitted` with "verified: Applied badge".
- Dice postings often show the recruiter's name, email or phone. Copy the contact into the tracker
  notes for follow-ups. Never message or call anyone from Dice.

## Notes

- Many Dice postings come from staffing vendors for an end client. If two vendors post the same role
  for the same client, apply once (dupe-check by company and role, and compare the descriptions).
- Contract postings name C2C, W2 or 1099 in the employment type or the description. Check them
  against `work_authorization.employment_models` before applying.
