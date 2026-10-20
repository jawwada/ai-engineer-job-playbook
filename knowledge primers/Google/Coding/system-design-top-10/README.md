# System Design Top 10: ten systems that cover the whole space of decisions

An interactive page (open in a browser) for Google-style system design interviews. Ten systems were chosen for popularity and for diversity of the design decisions they force: an API rate limiter, TinyURL, Twitter/Reddit (feeds, timelines, comment trees, ranking), WhatsApp, Google Docs, Uber, Google Maps, Google Drive, a distributed message queue, and a distributed key-value database. Each system has six tabs: requirements (functional and non-functional) with scale estimates derived out loud; the APIs, each explained in a line; the design choices with the options considered and the rationale; a system diagram with a request walk-through; the algorithms and data structures, what each one does and where it fits; and the follow-up questions an interviewer pushes on, with one-breath answers.

Three reference cards sit beside the systems: the 45-minute structure with time boxes, what the rubric grades, and an estimation cheat sheet (latency, throughput, conversions, availability); the building blocks and the trade-off sentence for each (data and consistency, scaling and caching, communication and reliability); and an algorithm index that lists every algorithm on the page with the systems it belongs to, plus a "how would you..." lookup.

## Files

| File | What it is |
|---|---|
| `system-design-top-10.html` | The page: 13 cards, 69 tabs, 10 diagrams. Self-contained; loads fonts from Google Fonts when online and falls back to system fonts offline. |

## Related

- Chapters on system design and the five role-related-knowledge topics in `book/`.
- `knowledge primers/Distributed_Systems_by_Design.pdf` and `knowledge primers/Designing_Agentic_Systems.pdf`.
- `knowledge primers/toloka-fde-final-round/scoping-and-pricing-playbook.html` for the agentic gym and coding-environment designs as data products.

## How it was built

Written on 19 October 2026 from the publicly described designs (Twitter's hybrid fan-out, Dropbox's block sync, Uber's H3 and dispatch, Google's OT-based Docs, Kafka's log and ISR replication, Dynamo and Cassandra, contraction hierarchies for routing, the Signal protocol) and standard back-of-envelope numbers. Figures are rules of thumb for estimation, not any company's current internals.
