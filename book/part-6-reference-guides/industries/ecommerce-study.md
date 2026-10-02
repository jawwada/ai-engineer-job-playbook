# A Study of Ecommerce

*A structured reference on how online commerce works — from the moment a shopper (or, increasingly, their AI agent) discovers a product to the moment it's delivered, paid for, and possibly returned — and the data, systems, and players that make it happen.*

---

## 1. Orientation: the order as the unit, and two clocks

Ecommerce is the business of selling goods and services over digital channels. Strip away the storefronts and logistics and it is fundamentally a system for converting **intent** into a **fulfilled, paid order** — and then doing it again, profitably, at scale. Every concept in this study is a stage in, or a support system for, that conversion.

Two mental models help:

- **Two clocks.** A *real-time path* runs in the shopper's session — discovery, browsing, cart, checkout, payment authorization — measured in seconds, where milliseconds of latency and grams of friction cost conversions. A *back-office path* runs from minutes to weeks — inventory, fulfillment, shipping, settlement, returns, analytics. The two are joined by **the order** (the canonical record of who bought what) and **product data** (the shared description of what's for sale).
- **The value chain.** discovery → consideration → purchase → fulfillment → post-purchase, with a technology stack, payment rails, and logistics network wrapped around every stage, and regulation/trust framing the whole thing.

A simplified flow of a single transaction:

```
Shopper has a need
  → Discovery        finds the product (search, social, ads, marketplace, AI agent)
     → Consideration  compares, reads reviews, checks price/stock
        → Cart        adds items; the order takes shape
           → Checkout authenticate/guest, address, shipping option
              → Payment authorize → capture funds across the card/wallet rails
                 → Order confirmed; inventory decremented
     → Fulfillment   pick, pack, ship from warehouse / store / 3PL
        → Delivery   last-mile to the door
           → Post-purchase  tracking, support, reviews, returns, loyalty, repeat
  ⇅ Commerce stack (storefront, OMS, PIM, WMS, CRM, analytics) runs alongside
  ⇅ Trust, payments security, privacy, and tax frame everything
```

The rest of this document walks each domain roughly in order, then the systems, the players, regulation, and the 2026 landscape.

---

## 2. The lifecycle of an order

The single most useful object to understand is the **order** and the journey that produces it — the ecommerce analog of an ad impression or a network connection.

```
Intent              shopper (or their AI agent) has a goal
  → Discovery       a product surfaces via search/social/ads/marketplace/AI
  → Product view    detail page: images, price, variants, reviews, stock
  → Add to cart     a provisional order; ~70% of carts are abandoned here
  → Checkout        identity (account/guest), shipping address & method, taxes
  → Payment auth    funds authorized in real time; fraud checks run
  → Order placed    inventory reserved/decremented; confirmation sent
  → Fulfillment     pick → pack → ship (own warehouse, store, or 3PL)
  → In transit      carrier handoff, tracking, last-mile delivery
  → Post-purchase   delivery confirmation, support, reviews
  → Returns         (often) reverse logistics; refund or exchange
  → Retention       loyalty, re-engagement, repeat purchase
```

Two metrics dominate this funnel. **Conversion rate** (share of visits that become orders, typically only ~2–3%) and **cart abandonment** (~70%) explain why so much engineering and design effort targets the cart-to-confirmation stretch. And the economics turn on **AOV** (average order value), **CAC** (customer acquisition cost), and **LTV** (lifetime value): a business is healthy when LTV comfortably exceeds CAC and repeat purchases amortize the cost of acquisition.

---

## 3. Product and catalog data: the schemas of commerce

If adtech keys on the bid request and telecom on the IMSI, ecommerce keys on the **product record**. Getting product data right is the substrate everything else stands on — and in 2026 it has become the difference between being visible to AI shopping agents or invisible to them.

### 3.1 The identifier system

| Identifier | What it names | Note |
|---|---|---|
| **SKU** | A specific sellable item, internal to the seller | Stock Keeping Unit; the merchant's own code |
| **GTIN / UPC / EAN** | A globally standardized product identity | The barcode standard; shared across sellers |
| **MPN** | Manufacturer Part Number | Ties a listing to the maker's catalog |
| **ASIN** | Amazon's internal product ID | Marketplace-specific |
| **Variant** | A specific size/color/configuration | Hangs under a parent "product" |
| **Order ID / line item** | The transaction and its contents | The canonical commercial record |

### 3.2 The product information model

A product record bundles the title, descriptions, **attributes** (size, color, material, specs), pricing (list, sale, currency, per-region), inventory/stock status, images and rich media, categorization/taxonomy, shipping dimensions and weight, and compliance data. This is managed in a **PIM** (Product Information Management) system, with images and video in a **DAM** (Digital Asset Management) system.

### 3.3 Structured data and feeds

Beyond the human-facing page, products are published as **machine-readable feeds** (e.g., merchant feeds for shopping channels) and marked up with **structured data** (schema.org `Product`). Historically this fed search engines and comparison shopping; in 2026 it is the **prerequisite for agentic commerce** — AI agents evaluate feeds and execute against APIs, so a complete, accurate, real-time product feed now matters more for discoverability than top-of-funnel content. Retailers whose data isn't machine-readable risk becoming invisible to AI shopping assistants.

---

## 4. Identity and the customer

- **Account vs guest:** shoppers either authenticate (an account with saved addresses, payment, and history) or check out as a guest. Forcing account creation is a notorious conversion killer, so most stores offer guest checkout.
- **Customer identifiers:** a customer ID, email (the durable cross-session key), phone, device/cookie identifiers, and per-visit session IDs. Loyalty programs add a membership ID that ties offline and online behavior together.
- **The profile:** order history, browsing behavior, wishlist, preferences, and lifetime value — the basis for personalization and segmentation, typically unified in a **CDP** (Customer Data Platform).
- **The privacy overlap with adtech:** ecommerce sits downstream of the same identity disruption — third-party cookie erosion, consent requirements, and signal loss — which has pushed retailers hard toward **first-party data** and logged-in relationships, and underpins the rise of retail media (§5, §12).

---

## 5. Discovery and merchandising

Getting in front of the shopper is half the business, and the channels have multiplied.

- **Owned search & SEO:** organic discovery via search engines and the site's own search/merchandising. Increasingly mediated by AI-generated answers rather than blue links.
- **On-site merchandising & recommendations:** search relevance, category curation, and recommendation engines ("you may also like," "frequently bought together") — a major personalization surface.
- **Paid media & retail media:** classic performance ads, plus the fast-growing **retail media networks (RMNs)** — retailers monetizing their own high-intent traffic and first-party data by selling ads (Amazon Ads, Walmart Connect, and many others). RMNs are among the highest-margin, fastest-growing parts of retail and the clearest convergence point between commerce and adtech.
- **Marketplaces vs DTC:** sellers choose between **marketplaces** (Amazon, Walmart, Alibaba/Tmall, Temu, Shein — reach and traffic, but commissions and less control) and **direct-to-consumer** storefronts (control of brand, data, and margin, but you must drive your own traffic). Most run a portfolio of both.
- **Social and live commerce:** discovery and checkout collapsing into social feeds — shoppable posts, creator/influencer-driven sales, and **livestream shopping**, led by TikTok Shop and the Chinese super-apps.

---

## 6. The cart and checkout

The cart is a provisional order; checkout is the highest-stakes, most-optimized stretch of the funnel.

- **The cart model:** a session-bound (or account-bound) collection of line items with quantities, applied promotions, estimated shipping and tax, and a running total. Persistent carts let shoppers resume across devices.
- **Checkout flow:** identity (account/guest) → shipping address → shipping method → payment → review → place order. Every additional field or step measurably reduces conversion, which is why **express checkouts** (Shop Pay, Apple Pay, Google Pay, PayPal) that pre-fill everything are so valuable.
- **Abandonment drivers:** unexpected shipping costs, forced account creation, long or confusing flows, limited payment options, and security doubts. Reducing friction here is among the highest-ROI work in ecommerce.

---

## 7. Payments

Behind a single "Pay" tap sits a multi-party settlement chain that moves money and manages risk.

### 7.1 The payment flow and its actors

| Actor | Role |
|---|---|
| **Payment gateway** | Captures and encrypts payment details at checkout |
| **Payment processor / PSP** | Routes the transaction (e.g., Stripe, Adyen, PayPal) |
| **Acquiring bank** | The merchant's bank that receives funds |
| **Card networks** | Visa, Mastercard, Amex — the rails and rules |
| **Issuing bank** | The shopper's bank that approves and funds the charge |
| **Merchant of record** | The entity legally responsible for the sale, tax, and disputes |

The flow: details captured → **authorized** (issuer confirms funds) → **captured** (funds committed, often at shipment) → **settled** (money moves) → potentially **refunded** or **charged back**.

### 7.2 Methods, security, and risk

Payment **methods** span cards, **digital wallets**, **Buy Now Pay Later (BNPL)**, account-to-account/bank transfers, and emerging options. Security and compliance hinge on **PCI DSS** (the card-data security standard), **tokenization** (replacing card numbers with tokens so merchants never store the raw data), and strong authentication (**3-D Secure**, and **SCA** under Europe's PSD2). Risk management covers **fraud detection**, **chargebacks** (including "friendly fraud" where legitimate buyers dispute charges), and refund handling — a material cost center, with global ecommerce fraud losses running into the tens of billions of dollars annually.

---

## 8. Fulfillment and the supply chain

The physical (or digital-goods) delivery that makes the order real — and where margins are often won or lost.

- **Inventory:** stock levels across locations, safety stock, demand forecasting, and the avoidance of both stockouts and dead inventory.
- **Order routing & the OMS:** the **Order Management System** decides how and from where to fulfill each order (which warehouse, store, or supplier), and orchestrates the downstream steps.
- **Warehousing & the WMS:** the **Warehouse Management System** runs pick-pack-ship; increasingly automated, with hundreds of thousands of facilities now using robotics.
- **Fulfillment models:** own warehouses, **3PL** (third-party logistics), marketplace-operated fulfillment (e.g., Fulfilled-by-Amazon), and **dropshipping** (the supplier ships directly, the seller never holds stock).
- **Last-mile delivery:** the carrier handoff and final leg to the door — the most expensive and most service-defining part; same-day/next-day expectations keep rising.
- **Reverse logistics (returns):** returns are a defining ecommerce cost, especially in apparel; handling refunds, exchanges, restocking, and fraud is now a strategic discipline, not an afterthought.

---

## 9. The commerce technology stack

The systems layer — the ecommerce analog of telecom's OSS/BSS or energy's control systems — turns a catalog into a running business.

- **Storefront / commerce platform:** the engine that renders the store and processes orders (Shopify, and a spectrum of SaaS and enterprise platforms). The build-vs-buy and platform choice shapes everything downstream.
- **Monolith vs headless / composable:** traditional all-in-one platforms vs **headless** architectures that decouple the front-end experience from the commerce back-end via APIs, and **composable / MACH** (Microservices, API-first, Cloud-native, Headless) stacks assembled from best-of-breed services. Adoption of API-first/headless approaches has become mainstream as brands chase omnichannel consistency.
- **The supporting systems:** **PIM** (products), **OMS** (orders), **WMS** (warehouse), **CRM** (customers), **ERP** (finance/operations), **CDP** (unified customer data), plus **analytics** and experimentation. Keeping these in sync — a single source of truth for product, inventory, and customer — is the core data-integration challenge.
- **The measurement problem (new in 2026):** AI-mediated purchases break click-and-session analytics. When discovery and comparison happen inside an AI assistant and the shopper arrives pre-decided (or the agent buys directly), traditional attribution loses visibility — a live, unsolved gap in the stack.

---

## 10. Actors and business models

- **Merchants/brands:** the sellers — from solo entrepreneurs on a SaaS storefront to global brands running DTC plus marketplace plus retail presence.
- **Marketplaces & platforms:** Amazon, Pinduoduo (the largest by GMV globally), Alibaba/Tmall, Temu, Shein, Walmart, and platform providers like Shopify that power millions of independent stores.
- **B2B ecommerce:** business-to-business is actually far larger than consumer retail ecommerce by transaction value, with its own dynamics — negotiated pricing, quotes, purchase orders, and long relationships.
- **Enablers:** payment providers, 3PLs and carriers, agencies and system integrators, review and personalization vendors, and aggregators.
- **Channel strategy:** the dominant pattern is **omnichannel** — a consistent experience across web, mobile app, social, marketplace, and physical store, with fulfillment options like **BOPIS** (buy online, pick up in store) and ship-from-store blurring the online/offline line.

---

## 11. Trust, regulation, and governance

Commerce runs on trust, and a thick layer of rules enforces it.

- **Consumer protection:** disclosure, refund/return rights, distance-selling rules, truth in advertising, and protections against dark patterns.
- **Payments & data security:** **PCI DSS** for card data; breach-notification obligations; strong-authentication mandates.
- **Privacy:** GDPR, CCPA/CPRA, and a growing patchwork governing consent, profiling, and first-party data use — the same regime that reshaped adtech.
- **Tax:** sales tax/VAT/GST collection and remittance across jurisdictions (a major complexity for cross-border sellers, e.g., post-*Wayfair* US economic-nexus rules and EU VAT schemes).
- **Product & marketplace compliance:** product safety, labeling, restricted goods, counterfeit controls, and marketplace-seller accountability.
- **Authenticity & accessibility:** fake-review enforcement and accessibility requirements for storefronts.

---

## 12. The 2026 state of play

A snapshot of where the industry sits and where it's heading. *(These figures move fast and vary across sources — treat them as directional ranges rather than precise counts.)*

- **Scale and maturity.** Global retail ecommerce is on the order of **$6.8–7.4 trillion** in 2026, roughly **20–22% of total retail sales**, with the U.S. market around **$1.3 trillion** (~18–22% of U.S. retail). B2B ecommerce is far larger again by transaction value. Growth has normalized to high-single-digit rates after the pandemic surge, and inflation has made shoppers notably more price-sensitive.
- **Agentic AI commerce — the defining shift.** AI shopping agents that research, compare, and (increasingly) transact are reshaping the front of the funnel. A cluster of competing standards emerged — OpenAI/Stripe's **Agentic Commerce Protocol (ACP)**, Google's **Universal Commerce Protocol** and **Agent Payments Protocol (AP2)**, plus **Visa Trusted Agent** and **Mastercard Agent Pay**. The practical 2026 settlement is *"AI handles discovery; merchants retain checkout"*: OpenAI scaled back native in-chat checkout in early 2026 in favor of protocol-based hand-offs to merchant environments, while Google rolled out agentic "Buy for me" checkout in Search/Gemini with early retail partners. AI-referred traffic to retail sites grew several-fold year over year and converts better than average, though it's still small in absolute volume — and Amazon is betting on proprietary agents (Rufus, "Buy for Me") while litigating against unauthorized agent scraping. Analysts project agentic commerce could reach hundreds of billions to a few trillion dollars in influenced/handled spend by 2030. The strategic takeaway for sellers: machine-readable product data and reliable checkout APIs are now table stakes.
- **Social and live commerce.** Now a core channel rather than an experiment — a multi-trillion-dollar global market, with TikTok Shop a standout and social commerce approaching ~9–10% of U.S. ecommerce. Content, discovery, and checkout are collapsing into one experience.
- **Retail media networks** continue to surge as retailers monetize first-party data and high-intent traffic, concentrating spend on the largest players.
- **Composable & headless** architectures are now mainstream as brands pursue omnichannel consistency and faster iteration.
- **Payments innovation** — BNPL, express wallets, and account-to-account methods keep expanding, alongside agentic payment credentials with spending caps and merchant controls.
- **Returns and unit economics** are under intense scrutiny as free-returns culture meets margin pressure, making reverse logistics a strategic priority.

---

## 13. Quick Reference: the domain at a glance

| Domain | What it does | Key concepts / data | Central tension |
|---|---|---|---|
| **The order** | The unit of the business | Conversion rate, AOV, CAC, LTV, cart abandonment | Turning intent into profitable, repeat orders |
| **Product data** | Describe what's for sale | SKU, GTIN/UPC, variants, PIM, structured feeds | Machine-readability for AI discovery |
| **Identity** | Know the customer | Account vs guest, email, CDP, loyalty | First-party data amid privacy loss |
| **Discovery** | Get in front of shoppers | SEO, recommendations, retail media, social/live | Channel mix; AI-mediated discovery |
| **Cart & checkout** | Close the sale | Cart model, express checkout, friction | Conversion vs verification |
| **Payments** | Move money, manage risk | Gateway/processor/networks, PCI DSS, fraud | Frictionless UX vs security |
| **Fulfillment** | Deliver the goods | Inventory, OMS/WMS, 3PL, last-mile, returns | Speed & cost; returns economics |
| **Commerce stack** | Run the business | Platform, headless/MACH, PIM/OMS/CRM/ERP | Single source of truth; broken attribution |
| **Actors & models** | Who sells & how | Marketplace vs DTC, B2B, omnichannel | Reach vs control vs margin |
| **Trust & regulation** | Keep it lawful & safe | Consumer law, privacy, tax, PCI | Compliance across jurisdictions |

---

### A note on scope
This study is deliberately structural — it maps *what online commerce is made of, how an order and its money and goods flow, and who the players are*. It can go deeper in several directions depending on your goal: a payments-and-fraud deep-dive (the settlement chain, PCI, chargeback mechanics), a data-and-platform architecture treatment (PIM/OMS data models, headless/composable design), an agentic-commerce strategy brief (protocols, feed readiness, measurement), a logistics/supply-chain angle, or a marketplace-vs-DTC growth analysis. Tell me which and I can expand that section. As with any fast-moving market, the 2026 figures here are drawn from industry and analyst sources that revise frequently, so treat specific numbers as directional.
