# LinkedIn Easy Apply playbook

Start: `https://www.linkedin.com/jobs/view/<id>/` in a new tab. The user is already signed in. At a
sign-in page, security check or CAPTCHA, stop and hand over.

## Before clicking Easy Apply

- The button must read **Easy Apply**. A plain **Apply** (with an arrow icon) leaves LinkedIn: record
  the target as `apply_url` and follow ats.md instead. It does not count toward `linkedin_max_per_day`.
- "Applied <time> ago" on the page means this job is done: record `submitted` with a note (or
  `needs-check` if the tracker had no record of it) and stop.
- "No longer accepting applications": record `skipped`.

## Page helper

Inject it once per page load: read `linkedin-helper.js` and run its full text with the JavaScript
tool in this tab. It returns "jobHelper ready". Then:

- `jobHelper.inspect()` lists the visible fields in the dialog (label, type, required, current value,
  options, validation error), the step title, progress, visible buttons, and whether "Follow company"
  is ticked. Run it on every step, before and after filling.
- `jobHelper.exposeFile()` makes the hidden resume `<input type="file">` visible so that find or
  read_page returns a ref for the upload tool.

The helper has no click, fill or submit function, by design.

## Steps in the dialog (order and labels vary)

1. **Contact info**: email (select the profile email), phone country code (United States (+1)),
   mobile phone (digits from `identity.phone`). Leave name and photo alone.
2. **Resume**: run `jobHelper.exposeFile()`, find the file input, and upload the tailored PDF with
   the upload tool. Then check that the new file is the selected resume; an older upload may still
   be selected, so select the new one. If a cover-letter upload is offered, give it the tailored
   cover letter PDF.
3. **Additional questions**: answer from answers.yaml, answers.md or skills_years only. Numeric
   "years" fields take whole numbers ("3", not "3 years"). For radio buttons and selects, pick the
   option whose text matches the answer. Re-run `inspect()` and fix any field that shows an error,
   such as "Please enter a valid answer" or "Enter a whole number between 0 and 99".
4. **Work authorization and sponsorship**: from answers.yaml.
5. **Voluntary self-identification**: "I don't wish to answer" or the closest decline option.
6. **Review your application**: scroll to the bottom and untick "Follow <Company> to stay up to date
   with their page" (set the checkbox to false with form_input), then confirm that
   `followCompanyChecked` is false in `inspect()`.
7. Review mode stops here, with the **Submit application** button visible. In auto mode, or after the
   user says "submit <id>", click **Submit application**.

## After submitting

- Expect "Your application was sent to <Company>" and click **Done**.
- Answer every prompt to update the profile, add skills, turn on alerts, share the news or save the
  resume to the profile with **Not now**, or dismiss it. Never accept a profile change.
- Verify: open `https://www.linkedin.com/my-items/saved-jobs/?cardType=APPLIED`. The job should be at
  the top. Record `submitted` with "verified in Applied list".

## Leaving an application unfinished

Closing the dialog asks "Save this application?". Choose **Save** when the user will finish it
(`needs-check`) and **Discard** when the posting is being skipped.

## Limits

- Every submission counts toward both `max_applications_per_day` and `linkedin_max_per_day`.
- "You've reached today's Easy Apply limit", "unusual activity" or any verification page: stop
  LinkedIn for the day, leave the remaining rows `tailored`, and tell the user.
- Never touch the profile, Open to Work, job-alert settings or resume settings.
