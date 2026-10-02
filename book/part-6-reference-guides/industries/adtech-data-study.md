# A Study of AdTech Data

*A structured reference on the data that flows through the digital advertising ecosystem — from the moment a page loads to the moment a campaign is measured.*

---

## 1. Orientation: data as the substance of adtech

Digital advertising is, at its core, a data-processing pipeline that runs in the ~100–300 milliseconds between a user requesting a web page or app screen and an ad rendering in front of them. Every concept you listed — requests, users, audiences, targeting, supply-side and demand-side data, campaigns, filtering — is a category of data that is created, enriched, transmitted, matched, or acted upon during that window or in the batch processes that surround it.

It helps to hold two mental models at once:

- **The real-time path (RTB / programmatic):** an ad opportunity is detected, described as data, auctioned, won, and filled in milliseconds. This is where *requests*, *bid requests/responses*, and *filtering* live.
- **The offline / batch path:** audiences are built, segments are modeled, campaigns are configured, identity graphs are stitched, and measurement is reconciled — typically in data warehouses, clean rooms, and DMPs/CDPs over hours or days.

The two paths are joined by **identity** (a stable or probabilistic key for "who is this") and **taxonomy** (a shared vocabulary for "what is this audience/content/context"). Most of the hard problems in adtech data are really identity or taxonomy problems in disguise.

A simplified flow of a single impression:

```
User loads page/app
   → Publisher ad slot fires an Ad Request
      → SSP / Ad Exchange constructs a Bid Request (OpenRTB)
         → enriched with User, Device, Geo, Audience segments
            → broadcast to many DSPs
               → each DSP runs Filtering + Targeting + bid logic
                  → returns Bid Response (price + Ad Content/markup)
      → Auction resolves → winner's creative is served
         → Impression / click / conversion events flow back
            → Measurement, attribution, billing, optimization
```

The rest of this document walks each data domain in roughly the order data is created and consumed.

---

## 2. The Ad Request and the Bid Request

### 2.1 The ad request (publisher → ad server / SSP)

The **ad request** is the first data artifact. When a page or app loads an ad slot, the publisher's ad tag or SDK fires a request that says, in effect, "I have inventory available here." Minimum useful contents:

- **Inventory descriptor:** site/app ID, page URL or app bundle, the specific ad unit/placement ID, slot dimensions, and ad format (banner, video, native, audio).
- **Page/app context:** referrer, page category, keywords, content metadata, language.
- **Technical context:** user agent, IP address, screen size, connection type, supported APIs.
- **Identifiers available at request time:** cookies, mobile advertising IDs, universal/seller-defined IDs, consent strings.

### 2.2 The bid request (the standardized data object)

When the request enters programmatic, the SSP/exchange translates it into a **bid request**, almost always in the **IAB OpenRTB** format (OpenRTB 2.x is the dominant on-the-wire spec; 3.0 reorganizes it but adoption is partial). OpenRTB is the single most important data schema to understand, because it is the lingua franca that every DSP reads. Its principal objects:

| Object | Purpose | Representative fields |
|---|---|---|
| `BidRequest` | Top-level envelope | `id`, `at` (auction type), `tmax` (timeout), `cur`, `test` |
| `Imp` (Impression) | The thing being sold | `id`, `bidfloor`, `bidfloorcur`, `banner`/`video`/`native`/`audio`, `pmp` (deals), `secure` |
| `Site` / `App` | Where it appears | `id`, `domain`, `cat` (IAB categories), `page`, `bundle`, `publisher` |
| `Device` | The hardware/software | `ua`, `ip`/`ipv6`, `geo`, `make`, `model`, `os`, `osv`, `devicetype`, `ifa` (ad ID), `dnt`/`lmt` (do-not-track / limit-ad-tracking), `connectiontype` |
| `Geo` | Location | `lat`, `lon`, `country`, `region`, `city`, `zip`, `type` (GPS vs IP-derived) |
| `User` | Who | `id`, `buyeruid`, `yob`, `gender`, `data` (segments), `eids` (extended IDs) |
| `Data`/`Segment` | Audience attached to user | `id`, `name`, `segment[].id/value` |
| `Regs` / `User.consent` | Compliance signals | GDPR flag, US privacy/GPP string, COPPA flag |
| `Source` | Supply chain provenance | `schain` (supply chain object), `pchain` |
| `Pmp` / `Deal` | Private marketplace terms | `deal.id`, `at`, `bidfloor`, `wseat` |

The **bid response** (`BidResponse` → `SeatBid` → `Bid`) carries the buyer's answer: `price`, the creative (`adm` markup or `nurl`), `crid` (creative ID), `adomain` (advertiser domain, used for blocklists), `cat`, `attr` (creative attributes), and win/billing notice URLs.

**Why this matters as data:** the bid request is the richest single packet of behavioral, contextual, and identity data in the ecosystem, and it is broadcast to potentially dozens of bidders per impression. This breadth is precisely why "bid stream data" is both commercially valuable and a privacy flashpoint — regulators and IAB policy have progressively restricted things like precise geo and full IP in the bid stream.

---

## 3. Users and Identity

"User data" is really two questions: **who is this** (identity) and **what do we know about them** (audience, §4). Identity is the harder and more contested half.

### 3.1 The identifier zoo

- **First-party cookies:** set by the publisher's own domain; durable, consented, increasingly the foundation of everything.
- **Third-party cookies:** historically the cross-site backbone — cookie syncing let each vendor map its own ID to others'. Match rates were chronically lossy (a 40–60% sync rate was considered *good*), and they are now blocked by default in Safari (ITP) and Firefox.
- **Mobile advertising IDs:** Apple **IDFA** (gated behind App Tracking Transparency opt-in since 2021) and Google **GAID/AAID**. App-side identity has been sharply curtained by ATT.
- **CTV / device IDs:** e.g., Roku RIDA, Samsung TIFA — the connected-TV equivalents.
- **IP address + user agent:** the basis of *probabilistic* / fingerprint-style matching; privacy-sensitive and increasingly restricted.
- **Universal / alternative IDs (deterministic):** built mostly from hashed, consented email/phone. The Trade Desk's **UID2** and its European **EUID**, LiveRamp's **RampID**, **ID5**, Lotame **Panorama ID**, publisher-provided IDs (**PPID**), and Prebid **SharedID**. These are the leading post-cookie path on the open web.
- **Cohort / non-ID signals:** contextual targeting, seller-defined audiences, and modeled signals that avoid per-user identity altogether.

### 3.2 Identity graphs

An **identity graph** is the database that stitches these scattered keys into a single representation of a person or household. It maps deterministic links (same login, same hashed email across sites) and probabilistic links (same device/IP/behavior cluster) into a graph whose nodes are identifiers and whose edges are "likely the same entity." Graphs power cross-device targeting, frequency capping, and attribution. Their two failure modes are **under-linking** (fragmentation, the same person seen as many) and **over-linking** (collapsing different people, e.g., a shared family device).

### 3.3 The current state (2025–2026): the cookie reprieve

This area moved significantly and is worth stating precisely:

- In **July 2024** Google reversed its plan to deprecate third-party cookies in Chrome, opting instead for a "user choice" approach; in **April 2025** it dropped even the dedicated choice prompt.
- In **October 2025** Google **shut down the Privacy Sandbox initiative**, retiring most of its APIs (Topics, Protected Audience, Attribution Reporting, etc.), citing low adoption and regulatory pressure. A small set of privacy/security features survive — **CHIPS** (partitioned cookies), **FedCM** (federated sign-in), and **Private State Tokens** (anti-fraud).
- **Net effect:** third-party cookies remain functional in Chrome for the foreseeable future, but their *reliability is eroding* through user opt-ins to enhanced privacy, and they are already gone on ~30% of traffic (Safari + Firefox). There is no single Google-blessed replacement, so identity in 2026 is deliberately **layered**: first-party data + one or more universal IDs + contextual signals + clean-room collaboration.

*(This section reflects developments through early 2026; because Google's posture here has reversed before, treat the specifics as a snapshot worth re-verifying.)*

---

## 4. Audience Data

Audience data is the **interpretation** layer on top of identity — the inferred or declared attributes used to decide whether someone is worth bidding on.

### 4.1 The three sourcing tiers

- **First-party data:** collected directly from owned channels (site/app behavior, purchases, CRM, logins). Highest trust, most durable, now the strategic center of gravity.
- **Second-party data:** another organization's first-party data, shared via a direct partnership or a clean room.
- **Third-party data:** aggregated and sold by data brokers/marketplaces (e.g., demographic, interest, in-market, intent segments). Most exposed to cookie loss and regulation; declining in reliability.
- **Zero-party data:** information the user *intentionally and proactively* provides (preferences, survey answers) — a useful distinction because consent is unambiguous.

### 4.2 Segments and taxonomies

A **segment** is a named, addressable group ("auto intenders," "households with children," "frequent travelers"). Each segment has an ID, a definition (the rules or model that populate it), a size/reach estimate, a recency/decay rule, and a price. Segments are organized under a **taxonomy** — a shared classification so that a buyer's "Sports > Soccer" means the same thing across vendors. The **IAB Audience Taxonomy** and **Content Taxonomy** (and **Seller-Defined Audiences**, which let publishers expose first-party segments using the standard taxonomy in the bid stream) provide this common vocabulary.

### 4.3 Where audience data is built and stored

- **DMP (Data Management Platform):** the classic engine for ingesting, segmenting, and syncing audiences — historically third-party-cookie-centric, now waning.
- **CDP (Customer Data Platform):** unifies first-party customer data into persistent profiles; the rising replacement as the industry pivots to owned data.
- **Data clean rooms:** privacy-preserving environments (Amazon Marketing Cloud, Google Ads Data Hub, Snowflake, LiveRamp, Databricks, Habu, and walled-garden rooms) where two parties match and analyze overlapping data **without exposing raw PII**. They are central to the post-cookie strategy but have real limits: they still need an identity backbone, and the overlap between two modest datasets can be too small to be useful.

---

## 5. Targeting Data

Targeting is the set of rules and signals that decide *whether* to show an ad and *to whom*. The same dimensions appear on both the buy and sell sides; here is the full menu.

- **Demographic:** age, gender, income, education, household composition (mostly inferred/modeled).
- **Geographic:** country down to ZIP/postcode, radius/geofence, and DMA/media-market targeting; CTV adds household-level geo.
- **Contextual:** the content of the page/app itself — category, keywords, sentiment, and increasingly NLP/semantic analysis and image/video classification. Cookie-independent, so enjoying a renaissance.
- **Behavioral:** past browsing, app usage, purchase history → interest and in-market segments.
- **Retargeting / remarketing:** users who took a specific prior action (visited a product page, abandoned a cart).
- **Lookalike / modeled:** algorithmically expanded audiences resembling a seed set.
- **Device / technographic:** OS, device type, browser, connection, carrier.
- **Dayparting / temporal:** time of day, day of week.
- **Frequency / recency:** capping exposure per user over a period; requires stable identity.
- **Deal / inventory targeting:** specific publishers, placements, or PMP deal IDs.
- **Custom / data-onboarded:** an advertiser's own CRM list matched ("onboarded") to digital identifiers.

A useful framing: **inclusion** targeting (who you want) and **exclusion**/suppression (who you want to avoid — existing customers, converters, brand-unsafe contexts) are equally important and both implemented as data rules.

---

## 6. Supply-Side Data

The supply side represents the **seller** of inventory: publishers and the platforms that monetize them.

### 6.1 Core actors and their data

- **Publisher / ad server:** owns the inventory and the first-party relationship with the user. Holds page/content metadata, audience first-party data, and direct-sold campaign data.
- **SSP (Supply-Side Platform) / Ad Exchange:** packages publisher inventory, runs or routes the auction, and broadcasts bid requests. Produces inventory data, floor-price logic, and the supply-path metadata below.
- **Header bidding (e.g., Prebid):** a publisher-side technique that solicits bids from many demand sources *in parallel* before calling the ad server, improving yield and producing rich auction-level data.

### 6.2 Inventory and yield data

Key supply-side data objects: available impressions (forecasted and real-time), **floor prices** (static or dynamic), fill rate, **win rate**, **CPM/eCPM** and revenue by placement, viewability, and **bid density** (how many bidders respond). Yield management is fundamentally a data-optimization exercise over these signals.

### 6.3 Ad content and creative data (sell-side view)

The publisher must know *what* is allowed to render. Creative-related supply-side data includes accepted formats and dimensions, **creative attributes** (`attr` in OpenRTB), the **advertiser domain** (`adomain`), creative category (`cat`), and **blocklists** (`bcat`, `badv`, `bapp`) that the publisher attaches to requests to refuse certain advertisers, categories, or competitors. Creative scanning/quality vendors add malware, heavy-ad, and policy classifications.

### 6.4 Source and supply-chain transparency

"Source" data answers *where did this inventory come from and is it legitimate* — critical because of fraud and reseller opacity:

- **ads.txt / app-ads.txt:** publisher-published files declaring who is authorized to sell their inventory.
- **sellers.json:** the SSP-side counterpart declaring the seller/intermediary entities.
- **SupplyChain Object (`schain`):** an in-bid-request ledger of every hop the impression passed through.
- **Supply Path Optimization (SPO):** buyers' use of this data to pick the cleanest, cheapest path to the same impression and cut out redundant intermediaries.

---

## 7. Demand-Side Data

The demand side represents the **buyer**: advertisers, agencies, and the platforms that act on their behalf.

### 7.1 Core actors and their data

- **Advertiser / brand:** owns campaign objectives, budgets, first-party CRM data, and conversion definitions.
- **DSP (Demand-Side Platform):** the buying engine. Ingests bid requests, applies targeting and filtering, runs **bidding/pacing algorithms**, and returns bid responses. Holds the densest optimization data in the stack.
- **DMP/CDP and data partners:** supply the audience segments the DSP targets.
- **Ad server (buy side):** stores creatives, manages rotation, and logs delivery.

### 7.2 Campaign data

A **campaign** is the central buy-side data object. Its hierarchy is typically *Advertiser → Campaign → Line item/Ad group → Creative*. Campaign data includes:

- **Objectives & KPIs:** awareness (reach, CPM, viewability), consideration (CTR, CPC), or performance (CPA, ROAS, conversions).
- **Budget & flight:** total/daily budget, start/end dates, **pacing** strategy (even vs. accelerated).
- **Bidding strategy:** fixed CPM, or automated/algorithmic bidding toward a target CPA/ROAS.
- **Targeting config:** the §5 dimensions, attached as inclusion/exclusion rule sets.
- **Creative assignments:** which creatives run where, with what rotation and frequency caps.
- **Deal references:** any PMP/programmatic-guaranteed deal IDs the line item is allowed to transact on.

### 7.3 Filtering (the buy-side decisioning gate)

For every incoming bid request — and a large DSP evaluates *millions per second* — the DSP runs a cascade of **filters** before it ever computes a bid. This is where most requests are discarded. Typical filter stages:

1. **Eligibility / targeting match:** does this impression match any active line item's targeting? (Most requests fail here.)
2. **Budget & pacing:** is there budget left, and does pacing allow a bid now?
3. **Frequency capping:** has this user already seen the ad too many times?
4. **Brand safety & suitability:** category, keyword, and context exclusions; integration with verification vendors (e.g., IAB/GARM suitability tiers).
5. **Fraud / IVT filtering:** invalid-traffic detection — bots, data-center IPs, spoofed apps, declared via tools like ads.txt/sellers.json and IVT vendors.
6. **Inventory quality:** viewability thresholds, supply-path/`schain` checks, blocklists/allowlists.
7. **Consent & compliance:** does the consent string permit this processing for this vendor and purpose?
8. **Bid throttling / QPS management:** sampling to stay within infrastructure limits.

Only impressions surviving all filters reach the **valuation/bidding** model, which predicts value (e.g., probability of click/conversion × value) and sets a price.

### 7.4 Demand-side targeting vs. supply-side targeting

The same targeting *dimensions* (§5) appear on both sides, but the **intent differs**: the supply side uses targeting/eligibility to control *what it will accept and at what floor*, while the demand side uses targeting to control *what it will bid on and how much*. The auction is where these two rule sets meet.

---

## 8. Ad Blocking

Ad blocking is both a data-loss problem and a measurement problem.

- **Mechanisms:** browser extensions (e.g., filter-list blockers), browser-native blocking, DNS/network-level blocking (Pi-hole, ISP-level), and OS/app-level content blockers. They work primarily off **filter lists** (EasyList and similar) that match request URLs, element selectors, and known ad/tracker domains.
- **Data impact:** blocked requests never reach the SSP, so the impression simply *does not exist* in the bid stream — it is lost inventory and lost behavioral/identity signal. Estimates have long put blocked or signal-lost traffic in a meaningful double-digit share, compounding the losses from consent banners and cookie restrictions.
- **Measurement distortion:** blockers also strip analytics/measurement tags, so reported audience and conversion figures **undercount** real activity, and the undercount is non-random (skews toward technical, privacy-conscious users).
- **Responses:** acceptable-ads programs, **server-side tag management / first-party data collection** (routing events through the publisher's own domain so they aren't on a blocklist), lighter ad formats, and the broader pivot to first-party and contextual approaches that depend less on blockable third-party calls.

Treat ad blocking as one of several "signal attrition" forces — alongside consent opt-outs, ATT, and cookie restrictions — that systematically shrink and bias the data the rest of the stack runs on.

---

## 9. Measurement, Attribution, and the Feedback Loop

The pipeline is a loop: outcome data flows back to optimize the next bid. Key data objects:

- **Event data:** impressions, viewable impressions, clicks, video quartiles, conversions, post-view/post-click events.
- **Attribution:** assigning credit for conversions across touchpoints (last-touch, multi-touch, data-driven). Cookie loss has pushed attribution toward modeled/aggregated and clean-room-based approaches and **incrementality** testing (does the ad cause lift vs. a holdout?).
- **Verification:** third-party measurement of viewability, brand safety, and IVT.
- **Reconciliation/billing:** matching delivery logs across buy and sell sides; discrepancies between counts are a perennial data-quality issue.

---

## 10. Privacy, Consent, and Governance Data

Compliance is now a first-class data layer woven through every stage above.

- **Regulations:** GDPR/ePrivacy (EU), the patchwork of US state laws (CCPA/CPRA in California, plus Virginia, Colorado, and newer entrants like Maryland's MODPA and Kentucky's KCDPA effective 2025–2026), and others globally. They govern lawful basis, consent, data minimization, and user rights.
- **Consent signaling:** the IAB **Transparency & Consent Framework (TCF)** consent string, the US/global **GPP (Global Privacy Platform)** string, and **Global Privacy Control (GPC)** signals — all carried in the bid request and meant to be honored at every hop.
- **Consent Management Platforms (CMPs):** capture and store user choices and propagate them downstream.
- **Governance:** data lineage, retention limits, purpose limitation, and vendor allow/deny lists are increasingly themselves data assets that must be queryable and auditable.

---

## 11. Cross-Cutting Data Engineering Realities

Worth keeping in view, because they shape what is actually possible:

- **Latency budget:** the real-time path runs in roughly 100–300 ms, with per-bidder timeouts (`tmax`) often under 120 ms. This forces low-latency key-value stores for identity/profile lookup and aggressive precomputation; rich analysis happens offline.
- **Scale:** large DSPs/SSPs process **millions of bid requests per second**, so filtering early and cheaply (§7.3) is an architectural necessity, not just an optimization.
- **Identity is the join key for everything:** targeting, frequency capping, attribution, and audience all break down when identity is fragmented — which is exactly why the post-cookie transition touches every box in the diagram.
- **Taxonomy alignment is the silent tax:** mismatched audience/content taxonomies between partners cause silent reach loss and mis-targeting; the IAB taxonomies exist to reduce this.
- **Signal attrition is structural:** ad blocking + consent opt-outs + ATT + cookie restrictions mean the data is an increasingly **biased sample** of reality. Modeling and clean-room collaboration are the industry's answers, with the caveat that modeled data inherits the biases of its inputs.

---

## 12. Quick Reference: data domains at a glance

| Your topic | Where it lives | Primary data objects | Key tension |
|---|---|---|---|
| **Requests** | Publisher → SSP/exchange | Ad request, OpenRTB `BidRequest`/`Imp` | Richness vs. privacy of the bid stream |
| **Users** | Browser/app/DSP/graph | Cookies, MAIDs, universal IDs, identity graph | Stable identity post-cookie |
| **Ad blocks** | Client device | Filter lists, blocked-request gaps | Lost & biased signal |
| **Audience** | DMP/CDP/clean room | Segments, taxonomies, 1P/2P/3P data | Durable, consented audiences |
| **Targeting** | Buy & sell side rules | Inclusion/exclusion rule sets | Reach vs. precision vs. privacy |
| **Supply-side data** | Publisher/SSP | Inventory, floors, yield, `schain`, ads.txt | Transparency & fraud |
| **Ad content / source** | Sell side | Creatives, `adomain`/`attr`/`cat`, blocklists, sellers.json | Quality, safety, provenance |
| **Demand-side data** | Advertiser/DSP | Campaign hierarchy, bidding/pacing models | Efficient buying |
| **Campaign** | DSP/ad server | Objective, budget, flight, creatives, deals | KPI alignment |
| **Filtering** | DSP decisioning | Eligibility, budget, fraud, brand-safety gates | Throughput vs. accuracy |
| **Targetings** | Both sides | Same dimensions, opposite intent | Auction is the meeting point |

---

### A note on scope
This study is deliberately structural — it maps *what data exists, where, and why* across the ecosystem. It can be taken deeper in several directions depending on your goal: a field-by-field OpenRTB walkthrough, a data-engineering architecture (storage, latency, pipelines), a privacy/compliance deep-dive, or a market map of specific vendors. Tell me which and I can expand that section.
