# A Study of the Energy Domain

*A structured reference on how energy — especially electricity — is produced, moved, traded, and consumed: from the primary fuels in the ground to the second-by-second balancing of a continent-sized machine that cannot store its own product.*

---

## 1. Orientation: carriers, the instantaneous-balance constraint, and two clocks

Energy is the capacity to do work, and the energy *domain* is the system that converts raw **primary energy** (coal, gas, uranium, sunlight, wind, water) into useful **energy carriers** (electricity, refined fuels, heat, increasingly hydrogen) and delivers them where work needs doing. Electricity is the spine of the modern system because it is clean at the point of use, infinitely divisible, and the destination of more and more of the economy ("electrification"). It also has one defining, unforgiving property that shapes everything else:

**Electricity must be generated at the exact instant it is consumed.** The grid cannot, in bulk, store its own product. Supply and demand must match *continuously*, and any mismatch shows up immediately as a deviation in grid **frequency** (50 Hz in most of the world, 60 Hz in the Americas). This single constraint is why the power system needs real-time control, markets that clear by the minute, and a growing fleet of storage and flexibility.

Two useful models:

- **The plane/clock split.** A *real-time path* balances generation and load every few seconds (dispatch, frequency control, reserves). A *commercial/planning path* runs from minutes (markets) to decades (building plants and grids). They are joined by **metering/measurement** (how much was produced and consumed, by whom) and **price** (the signal that coordinates everyone).
- **The value chain.** Energy flows generation → transmission → distribution → consumption, with markets, control systems, and regulation wrapped around every link.

```
Primary fuels / resources
  → Generation (convert to electricity)
     → Transmission (move it far, at high voltage)
        → Distribution (step down, deliver locally)
           → End use (homes, industry, transport)
   ⇅ System operator balances supply = demand every second
   ⇅ Markets price it; metering measures it; OT/control systems run it
   ⇅ Regulation, decarbonization policy, and finance frame the whole thing
```

---

## 2. The lifecycle of an electron: the real-time balance

The clearest way to understand the industry is to watch a unit of demand get met in real time — the energy analog of a network connection or an ad impression.

```
Demand appears            a load switches on somewhere
  → Forecast              operators predict demand minutes-to-days ahead
  → Merit-order dispatch  cheapest available units are called first,
                          stacking up to meet the forecast
  → Generation responds   plants ramp; the marginal (last, most expensive)
                          unit sets the wholesale price
  → Transmission & losses  power flows from surplus to deficit regions;
                          ~5-8% is lost as heat along the way
  → Frequency control     tiny imbalances are corrected automatically
                          (inertia + governor response + regulation reserves)
  → Reserves              contingency reserves stand by for a plant tripping
  → Settlement            metered flows are reconciled and priced after the fact
```

Two foundational concepts fall out of this. **Merit order / economic dispatch:** generators are stacked from cheapest marginal cost (typically renewables and nuclear, near-zero fuel cost) to most expensive (gas peakers, oil), and dispatched in that order; the price almost everyone gets paid is set by the *marginal* unit needed to meet the last increment of demand. **Dispatchable vs variable:** coal, gas, nuclear, and hydro can be turned up or down on command; solar and wind produce when nature allows, which is why "balancing" gets harder as their share rises.

---

## 3. Primary energy and energy carriers

### 3.1 The primary sources

| Source | Type | Role | Note |
|---|---|---|---|
| **Coal** | Fossil | Baseload power, steel/cement | Highest-carbon; in structural decline in power but still large |
| **Natural gas / LNG** | Fossil | Flexible power, heat, industry | "Bridge" fuel; LNG enables global gas trade |
| **Oil** | Fossil | Mostly transport & petrochemicals | Minor in power generation today |
| **Nuclear (uranium)** | Low-carbon | Firm, dispatchable baseload | Reviving; SMRs an emerging design |
| **Hydropower** | Renewable | Dispatchable + storage (pumped) | Largest renewable generator historically |
| **Solar PV** | Renewable | Fast-growing variable generation | Now the largest source of new supply growth |
| **Wind (on/offshore)** | Renewable | Variable generation | Often peaks at night/season opposite solar |
| **Geothermal / bioenergy / others** | Renewable | Niche but firm/flexible | Geothermal is firm; bioenergy dispatchable |

### 3.2 Carriers and conversion

Primary energy is rarely useful directly. It is converted into **carriers**: **electricity** (the dominant and most flexible), **refined liquid fuels**, **heat/steam**, and **hydrogen** (an emerging carrier for hard-to-electrify uses like heavy industry and long-duration storage). A central theme of the modern system is **electrification** — shifting end uses (cars, heating, industrial process heat) from burning fuel directly onto the electric grid, which raises electricity demand even as total energy use flattens.

---

## 4. Generation

Generation converts primary energy into electricity, almost always by spinning a turbine that drives a generator (the exceptions being solar PV and fuel cells, which produce DC electricity directly). Key data concepts:

- **Capacity (kW/MW/GW):** the maximum instantaneous output — the *size* of a plant.
- **Capacity factor:** actual output over a period ÷ theoretical maximum. Nuclear runs ~90%+; solar might be ~15-25%; this gap is why nameplate capacity and actual energy delivered are very different numbers.
- **Baseload / mid-merit / peaking:** plants are characterized by how they're run — always-on cheap baseload, flexible mid-merit, and expensive fast-start peakers used only at demand peaks.
- **Firm vs variable:** a megawatt of gas is *firm* (available on demand); a megawatt of solar is *variable* — a crucial distinction the rest of the system must engineer around.

---

## 5. Transmission and distribution: the grid

The grid moves power from where it's made to where it's used, trading voltage for current to limit losses.

- **Voltage hierarchy:** generators feed a **step-up transformer** → **transmission** at high voltage (roughly 110–765 kV) carries bulk power long distances → **substations** step it down → **distribution** at medium/low voltage delivers to homes and businesses. Higher voltage = lower current = lower resistive loss, which is why long-distance lines run at hundreds of kilovolts.
- **AC vs HVDC:** the grid is overwhelmingly **alternating current** (which transformers can easily step up/down), but **high-voltage direct current (HVDC)** is used for very long distances, undersea links, and connecting asynchronous grids — increasingly important for offshore wind and intercontinental interconnectors.
- **Interconnection:** regional grids are linked into large synchronized areas so that surplus in one place can cover deficit in another, improving reliability and letting cheaper or cleaner generation reach more demand.
- **The grid as the binding constraint:** building transmission is slow, capital-intensive, and politically fraught. In 2026 the grid — not generation — is widely identified as the main bottleneck on connecting new clean energy and new demand alike; **interconnection queues** of projects waiting to connect have become a defining problem.

---

## 6. The system operator and balancing

Someone must keep supply and demand matched in real time and operate the bulk grid neutrally. That is the **System Operator** — a **TSO** (Transmission System Operator) in Europe, or an **ISO/RTO** (Independent System Operator / Regional Transmission Organization, e.g., PJM, MISO, ERCOT, CAISO) in much of North America.

Their core functions and the data behind them:

- **Frequency control:** automatic responses keep frequency at 50/60 Hz — physical **inertia** from spinning machines, fast **governor response**, and **regulation reserves**. As inverter-based solar/wind (which provide little natural inertia) grow, maintaining stability is an active engineering and market challenge.
- **Ancillary services:** the supporting products that keep the grid stable — frequency regulation, **spinning/non-spinning reserves**, voltage support, and **black-start** capability (the ability to restart the grid from a total blackout).
- **Reserves & adequacy:** holding enough margin to survive the largest credible contingency (a big plant or line tripping), and planning enough capacity for future peak demand.
- **Grid codes:** the technical rulebook every connected asset must obey.

---

## 7. Markets and commercial structure

How energy is bought, sold, and governed varies hugely by jurisdiction, but the building blocks are consistent.

### 7.1 Market structure

- **Vertically integrated (regulated):** one utility owns generation, wires, and retail in a franchise area, with prices set by a regulator. Common in parts of the U.S. and much of the developing world.
- **Unbundled / liberalized:** generation, transmission, distribution, and retail are legally separated to allow competition in generation and retail while the wires remain regulated monopolies. The model across the EU and U.S. restructured markets.

### 7.2 Wholesale markets

Electricity is traded across a sequence of time horizons that converge on real time:

- **Forward/futures:** months-to-years ahead, for hedging.
- **Day-ahead:** the main market; commits generation for each hour of tomorrow.
- **Intraday:** adjustments closer to delivery.
- **Real-time / balancing:** final reconciliation at the moment of delivery.
- **Capacity markets:** pay generators to *be available* in future years (selling firmness, not energy) — increasingly expensive as demand surges.
- **Ancillary-service markets:** price the stability products from §6.

Pricing is typically **marginal**: the last unit needed sets the clearing price for all. U.S. markets use **Locational Marginal Pricing (LMP)** — a different price at each grid node reflecting congestion and losses; Europe largely uses **zonal** pricing.

### 7.3 The actors

Generators (gencos), transmission owners, distribution network operators (DNOs/DSOs), retailers/suppliers, energy traders, **aggregators** and **virtual power plants** (which bundle many small assets into a market-facing block), large industrial offtakers signing **PPAs** (Power Purchase Agreements, often the financing vehicle for new renewables), and a growing population of **prosumers** (consumers with rooftop solar and batteries who both buy and sell).

---

## 8. Identity and the data of energy

Where adtech keys on cookies and telecom on the IMSI, the energy system keys on the **metering point** and the **market participant** — and on getting the *units* right.

### 8.1 The units distinction (the most important data point)

- **Power (kW, MW, GW):** an instantaneous *rate* — how fast energy flows right now.
- **Energy (kWh, MWh, GWh, TWh):** a *quantity* — power integrated over time.

A 1 MW solar farm (power) running 5 hours produces 5 MWh (energy). Confusing the two is the classic error in energy data work; nearly every settlement, bill, and forecast depends on keeping rate and quantity distinct.

### 8.2 Identifiers and metering

| Identifier | What it names |
|---|---|
| **Metering point ID** | A physical connection where energy is measured. UK uses **MPAN** (electricity) and **MPRN** (gas); the EU uses the **EIC** (Energy Identification Code); the U.S. uses utility account/premise/meter IDs |
| **Smart meter (AMI)** | Advanced Metering Infrastructure — interval meters that report consumption remotely, enabling time-of-use pricing and near-real-time data |
| **Market participant codes** | Identify each generator, supplier, and trader in market settlement |
| **Asset/resource IDs** | Identify dispatchable units and their telemetry in the operator's systems |

**Settlement** is the back-office process that reconciles metered flows against market positions and assigns who owes whom — the financial heartbeat analogous to telecom's CDR-to-billing pipeline.

---

## 9. Control systems and protocols (the operational-technology layer)

The grid is run by **operational technology (OT)** — a stack distinct from corporate IT, with its own protocols and severe reliability/security demands.

- **SCADA** (Supervisory Control and Data Acquisition): the real-time eyes and hands over substations and plants.
- **EMS / DMS / ADMS:** Energy Management Systems at the transmission level; Distribution Management Systems and **Advanced DMS** for the increasingly active distribution grid full of distributed resources.
- **Protocols:** **IEC 61850** (substation automation), **DNP3** (common in North American utilities), **Modbus**, **IEC 60870-5-101/104** (telecontrol), **OpenADR** and **IEEE 2030.5** (demand response and DER communication).
- **Cybersecurity:** the grid is critical infrastructure and a prime attack target; frameworks like **NERC CIP** in North America impose mandatory controls. The convergence of IT and OT, and the proliferation of internet-connected DERs, expand the attack surface.

---

## 10. Storage and flexibility

Because electricity can't be stored in bulk on the wires, **flexibility** — the ability to shift supply or demand in time — is the system's pressure-release valve, and it is the fastest-moving part of the industry.

- **Battery energy storage (BESS):** now the fastest-growing power technology. Roughly 108 GW of new battery storage was deployed worldwide in 2025 (about 40% more than 2024, ~11× the 2021 level), with **lithium-iron-phosphate (LFP)** chemistry making up ~90% of deployments and about 80% utility-scale; battery costs fell sharply again in 2025. China led with roughly 60% of additions. Batteries excel at short-duration shifting (hours) — e.g., storing midday solar for the evening peak.
- **Pumped-hydro storage:** still the largest installed energy-storage capacity globally; pumps water uphill when power is cheap and releases it through turbines when it's dear.
- **Demand-side flexibility:** **demand response** (paying consumers to reduce or shift load), **vehicle-to-grid (V2G)**, smart EV charging, and **virtual power plants** that orchestrate thousands of small assets.
- **The "duck curve":** the daily net-load shape created by solar — a midday dip and a steep evening ramp as the sun sets and demand stays high — which is precisely what storage and flexibility are deployed to smooth.

---

## 11. End use and demand

Demand is split across **residential**, **commercial**, **industrial**, and **transport** sectors, each with distinct load shapes. Two structural forces dominate the current outlook:

- **Electrification + efficiency:** EVs, heat pumps, and industrial electrification push electricity demand up, while efficiency gains partly offset it — the net effect is that electricity demand is growing again after a flat decade.
- **The data-center / AI surge:** AI and high-performance computing have turned data centers into a major new source of large, concentrated, around-the-clock load. Global data-center electricity use was on the order of ~415 TWh in 2024 (~1.5% of world electricity) and growing at roughly a 12% annual rate; in the U.S., about half of projected electricity-demand growth through 2030 is attributed to data centers. A single AI task can draw vastly more power than a conventional web query, and the clustering of these facilities strains local grids — visible in capacity-market prices (e.g., PJM's capacity price for the 2026–27 delivery year rose roughly tenfold versus two years earlier) and in proposals for local moratoria. "Speed to power" — how fast a site can secure grid connection — has become the binding constraint on AI buildout.

---

## 12. Decarbonization, policy, and governance

Climate policy is now woven through every layer.

- **Carbon pricing:** cap-and-trade systems (e.g., the EU Emissions Trading System) and carbon taxes put a price on emissions, reshaping the merit order.
- **Renewable mandates & certificates:** Renewable Portfolio Standards, **RECs** (Renewable Energy Certificates) / Guarantees of Origin that let buyers claim clean energy.
- **Emerging decarbonization tech:** **CCUS** (carbon capture, utilization, and storage), **low-emissions hydrogen**, and long-duration storage for the hard-to-abate last mile.
- **Regulators & institutions:** wholesale-market and interstate regulators (e.g., **FERC** in the U.S.), retail/distribution regulators (state **PUCs**; **Ofgem** in the UK; national regulators under **ACER** in the EU), and reliability bodies (**NERC** in North America). Policy levers include net metering, interconnection rules, and capacity-adequacy requirements.

---

## 13. The 2026 state of play: the "Age of Electricity"

A snapshot of where the system sits and where it's heading. *(These are fast-moving, recently reported figures — largely from IEA and Ember 2026 analyses — so treat specifics as a dated snapshot worth re-verifying.)*

- **Solar took the lead.** In 2025, solar PV was the single largest contributor to the growth in global energy supply (more than a quarter of the increase) — the first time on record a modern renewable led. Record renewable additions of roughly 800 GW were ~75% solar, and renewables' total output is now roughly matching coal's; in the EU, solar plus wind passed fossil generation for the first time.
- **Storage went mainstream.** Battery storage was the fastest-growing power technology, with annual additions exceeding the largest-ever annual additions of natural gas capacity — a structural turning point for integrating variable renewables.
- **Nuclear's revival.** Over 12 GW of new reactors began construction in 2025; more than 40 countries now include nuclear in their plans; and **small modular reactors (SMRs)** are drawing strong interest, notably from technology companies seeking firm, clean power for data centers, with first commercial units expected around 2030.
- **Demand is back — driven by data centers.** After a flat decade, electricity demand is rising again; AI/data-center load is the headline driver in advanced economies, making grid connection and capacity the scarce resources.
- **The grid is the bottleneck.** Investment has tilted decisively toward clean power, grids, and storage (the bulk of power-sector investment), with total energy investment around \$3.3 trillion in 2025 — yet grid build-out and interconnection queues remain the chief constraint on both new supply and new demand.
- **Affordability and security tension.** Household electricity prices have risen faster than incomes in many countries since 2019, and recent fossil-fuel shocks have sharpened the security case for domestic clean generation — even as the transition's pace and politics vary sharply by region.

---

## 14. Quick Reference: the domain at a glance

| Domain | What it does | Key concepts / data | Central tension |
|---|---|---|---|
| **Primary energy / fuels** | The raw input | Coal, gas/LNG, uranium, solar, wind, hydro | Carbon vs cost vs security |
| **Generation** | Make electricity | Capacity (MW), capacity factor, dispatchable vs variable | Firmness vs cost vs emissions |
| **Transmission** | Move bulk power far | High voltage, HVDC, interconnection, losses | Build speed; the binding constraint |
| **Distribution** | Deliver locally | Medium/low voltage, DSOs, DERs | Two-way flows from prosumers |
| **System operation** | Balance supply = demand | Frequency, inertia, reserves, ancillary services | Stability with low-inertia renewables |
| **Markets** | Price & coordinate | Day-ahead/real-time, LMP, capacity markets, PPAs | Marginal pricing vs investment signals |
| **Identity & metering** | Measure & settle | kW vs kWh, MPAN/EIC, smart meters (AMI), settlement | Data accuracy & granularity |
| **Control / OT** | Run the grid safely | SCADA, EMS/ADMS, IEC 61850, DNP3, NERC CIP | Reliability & cybersecurity |
| **Storage & flexibility** | Shift energy in time | BESS (LFP), pumped hydro, demand response, duck curve | Duration & cost of flexibility |
| **End use** | Where energy works | Residential/industrial/transport, electrification, data centers | Surging, concentrated new demand |
| **Decarbonization & policy** | Steer the transition | Carbon pricing, RECs, CCUS, regulators | Speed vs affordability vs reliability |

---

### A note on scope
This study is deliberately structural — it maps *what the energy system is made of, how power and money flow through it, and who balances and governs it*, with electricity as the spine. It can go deeper in several directions depending on your goal: a power-markets and trading deep-dive (dispatch, LMP, settlement mechanics), a grid-engineering treatment (AC/HVDC, stability, interconnection), an OT/data-and-protocols view (SCADA, metering data models, cybersecurity), a fuels/commodities angle (oil, gas/LNG, coal markets), or a decarbonization-policy analysis. Tell me which and I can expand that section.
