# Company ATS playbook (Greenhouse, Lever, Ashby, Workday and others)

## General rules

- Use the ATS form URL directly rather than a careers page that embeds the form in an iframe.
- Never use "Apply with LinkedIn", "Apply with Indeed", "Apply with Google" or ATS autofill
  accounts: they share profile data or create accounts. Fill the form directly.
- Many forms autofill from the uploaded resume. Re-check every autofilled field against `identity`
  and the master resume; parsers mangle names, phone numbers and dates.
- Location autocomplete: type the city from `identity.location` and pick the matching suggestion.
- EEO and voluntary self-identification: decline every question.
- Consent and privacy checkboxes: only with an `approved_consents` entry (SKILL.md, step 2.4).
- CAPTCHA, email verification code, "create an account" or "sign in to continue": stop, mark the row
  `needs-check` with the reason, and fill nothing more.
- ATS forms have no applied list. Verify with the confirmation page text and record it in the notes;
  a confirmation email usually follows.

## Greenhouse

URLs: `https://job-boards.greenhouse.io/<company>/jobs/<id>`, `https://boards.greenhouse.io/<company>/jobs/<id>`,
or a company careers page with `?gh_jid=<id>` (open the board URL instead).

One page: First name, Last name, Email, Phone, Location, Resume/CV (use Attach, which is a file
input, not "Enter manually"), Cover letter (attach the cover letter PDF if the field exists), LinkedIn
profile, website, custom questions (text, select, multi-select, yes/no), Voluntary Self-Identification,
then **Submit application**. Required fields are marked with *. Confirmation: "Thank you for applying"
or "Application submitted".

## Lever

URLs: `https://jobs.lever.co/<company>/<posting-id>` and `.../apply`.

Upload the resume first (it fills name, email, phone and current company), then check Full name,
Email, Phone, Current company, LinkedIn, GitHub, Portfolio and Other website. Paste the cover letter
text into "Additional information" (shorten if there is a limit). Answer custom questions, decline
the US EEO survey, then **Submit application**. An hCaptcha challenge sometimes appears on submit:
stop. Confirmation: an "Application submitted!" page.

## Ashby

URLs: `https://jobs.ashbyhq.com/<company>/<posting-id>` and `.../application`.

"Upload File" for the resume (autofill), then Name, Email, Phone, LinkedIn and custom questions
(often long-form text: answer only from answers.yaml or answers.md and leave the rest for the user),
EEO (decline), then **Submit Application**. A spam check or verification code: stop. Confirmation: a
success message on the same page.

## Workday (always stop)

URLs on `*.myworkdayjobs.com` or `*.myworkdaysite.com`. Applying requires creating an account or
signing in. Do not click Apply and do not prefill. Mark the row `needs-check` with "Workday: account
required, apply manually" and give the user the link.

## Other systems

iCIMS, Taleo, SuccessFactors, Oracle Recruiting, BrassRing, Jobvite, SmartRecruiters, Workable,
BambooHR and company-built portals follow the general rules. Most require an account or an email
verification; stop as soon as one is required.
