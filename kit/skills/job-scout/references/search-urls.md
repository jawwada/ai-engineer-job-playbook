# Search URLs for /job-scout

Build one URL per title and employment type. Take keywords from `targets.titles`, URL-encode them
(space = `%20`, quote = `%22`) and wrap multi-word titles in quotes to keep the phrase together,
for example `%22Forward%20Deployed%20Engineer%22`. Run the most important titles first.
These are the sites' public URL parameters as of October 2026 (the Dice ones were checked against
the live site). Sites change them: if a filter stops applying (the result page shows no active
filter chip), set it in the page UI and copy the new URL.

## LinkedIn (Easy Apply, remote, United States, newest first)

```
https://www.linkedin.com/jobs/search/?keywords=<KEYWORDS>&geoId=103644278&f_AL=true&f_WT=2&f_TPR=r172800&f_JT=C&sortBy=DD
```

| Parameter | Meaning | Values |
|---|---|---|
| `keywords` | search text | `%22AI%20Engineer%22`, `%22Forward%20Deployed%20Engineer%22` |
| `geoId` | location | `103644278` = United States |
| `f_AL` | Easy Apply only | `true` |
| `f_WT` | workplace type | `1` on-site, `2` remote, `3` hybrid |
| `f_TPR` | posted within, in seconds | `r86400` 24 h, `r172800` 48 h, `r604800` 7 days |
| `f_JT` | job type | `C` contract, `F` full-time, `P` part-time, `T` temporary; several: `C%2CF` |
| `sortBy` | order | `DD` most recent, `R` relevance |
| `start` | paging | `0`, `25`, `50` |

- Set `f_TPR` to `r` + `max_posting_age_hours * 3600`.
- `f_JT`: `C` when the profile accepts W2, C2C or 1099 contracts; `F` when it accepts full-time.
- Job id: the number in `/jobs/view/<id>/` or `currentJobId=<id>`. Tracker id `li-<id>`; canonical
  URL `https://www.linkedin.com/jobs/view/<id>/`.
- Cards show "x hours ago" and "Easy Apply". Promoted cards can be older than the filter; check
  each card's age. A card that says "Applied" is already done: skip it.

## Dice (remote, recent, by employment type)

```
https://www.dice.com/jobs?q=<KEYWORDS>&countryCode=US&filters.postedDate=ONE&filters.workplaceTypes=Remote&filters.employmentType=CONTRACTS%7CTHIRD_PARTY&page=1&pageSize=20&language=en
```

| Parameter | Meaning | Values |
|---|---|---|
| `q` | search text | as above |
| `filters.postedDate` | posted within | `ONE` today, `THREE` last 3 days, `SEVEN` last 7 days |
| `filters.workplaceTypes` | workplace | `Remote`, `Hybrid`, `On-Site` |
| `filters.employmentType` | type; several joined by `%7C` | `CONTRACTS`, `THIRD_PARTY`, `FULLTIME`, `PARTTIME` |
| `page`, `pageSize` | paging | `1`, `20` |

- Use `ONE` when `max_posting_age_hours` is 24 or less, otherwise `THREE`, and still check each
  posting's own age.
- `THIRD_PARTY` marks roles open to corp-to-corp through a third party; include it only when the
  profile accepts C2C. Add `FULLTIME` only when the profile accepts full-time.
- Job id: the UUID in `/job-detail/<uuid>`. Tracker id `dice-<uuid>`.

## Indeed (scouting only, never submit)

```
https://www.indeed.com/jobs?q=<KEYWORDS>&l=Remote&fromage=1&sort=date&sc=0kf%3Aattr%28DSQF7%29%3B&jt=contract
```

| Parameter | Meaning | Values |
|---|---|---|
| `q`, `l` | keywords, location | `l=Remote` or `l=United%20States` |
| `fromage` | days since posted | `1` (24 h), `3`, `7`, `14` |
| `sort` | order | `date` |
| `sc` | remote filter | `0kf:attr(DSQF7);` encoded as above |
| `jt` | job type | `contract`, `fulltime`, `parttime`, `temporary` |
| `start` | paging | `0`, `10`, `20` |

- Job id: `jk=<key>` in `viewjob?jk=<key>` (`vjk=<key>` on result pages). Tracker id `indeed-<key>`;
  canonical URL `https://www.indeed.com/viewjob?jk=<key>`.
- "Apply on company site" postings point to an ATS: record that URL as `apply_url`.

## Gmail job alerts

- Query: `label:<ID of Jobs/Alerts> newer_than:1d` (look the ID up with the list-labels tool).
- Typical links: LinkedIn `https://www.linkedin.com/comm/jobs/view/<id>/...` (id = `li-<id>`), Dice
  `.../job-detail/<uuid>`, Indeed tracking links that contain `jk=<key>`. Open a tracking link in
  Chrome only when the id cannot be read from the link itself; use the final URL.
- An alert received inside the freshness window counts as proof that its postings are fresh.

## ATS hosts you will meet

`boards.greenhouse.io`, `job-boards.greenhouse.io` (also `?gh_jid=<id>` on company sites),
`jobs.lever.co`, `jobs.ashbyhq.com`, `*.myworkdayjobs.com` (account required: never apply).
Tracker id `ats-<company>-<role>` when the posting was found directly on an ATS.
