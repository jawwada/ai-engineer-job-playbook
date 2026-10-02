# A Study of the Telecom Industry

*A structured reference on how a telecommunications network is built, operated, and monetized — from the moment a device powers on to the systems that bill for the traffic it generates.*

---

## 1. Orientation: layers, planes, and two clocks

A telecom network is a machine for moving information between endpoints with guaranteed reach, reliability, and accountability. Everything in the industry — radios, core software, SIM cards, billing systems, regulation — exists to answer four questions about any unit of traffic: *who is this, where are they, are they allowed, and who pays?*

Two mental models help:

- **The plane model.** Every network separates the **user plane** (the actual voice/data payload, the "bearer"), the **control plane** (signaling that sets up, moves, and tears down connections), and the **management plane** (configuration, monitoring, and orchestration). Most of the cleverness — and most of the hard problems — live in the control and management planes, not the payload.
- **Two clocks.** A *real-time path* runs in milliseconds: a device attaches, is authenticated, gets a session, and packets flow. A *back-office path* runs in seconds to days: provisioning, charging, billing, assurance, planning, and settlement. The two are joined by **identity** (a stable key for the subscriber and device) and **policy** (the rules for what that subscriber may do and at what quality).

It also helps to see the network as a stack of domains the traffic crosses:

```
Device  →  Access Network (RAN / fixed access)
        →  Transport (fronthaul / backhaul / metro / core transport)
        →  Core Network (mobility, sessions, policy, voice via IMS)
        →  Service Edge & Interconnect (internet, other operators, clouds)
        ⇅  OSS/BSS (provisioning, charging, billing, assurance) runs alongside all of it
        ⇅  Regulation, spectrum, and standards frame the whole thing
```

The rest of this document walks each domain roughly in the order traffic crosses it, then covers the actors, the support systems, regulation, and the 2026 state of play.

---

## 2. The lifecycle of a connection

The single most useful thing to internalize is what actually happens when a phone connects — it mirrors the structure of the whole industry.

```
Power on / enter coverage
  → Cell search & sync         device finds a radio cell (RAN)
  → Attach / Registration      device announces itself to the core
  → Authentication             SIM credentials checked against the operator's
                               subscriber database (mutual authentication)
  → Security setup             ciphering & integrity keys established
  → Session establishment      a data bearer (PDU session) is created;
                               an IP address is assigned
  → Policy & QoS applied       allowed services, speed tiers, quotas set
  → Traffic flows              user-plane packets routed to internet / IMS / peer
  → Mobility                   handovers as the device moves between cells
  → Charging                   usage metered (online/offline) for billing
  → Detach / release           session torn down, resources freed
```

Voice in modern networks is just a specialized session: it runs as **VoLTE** (Voice over LTE) or **VoNR** (Voice over New Radio) through the **IMS** (IP Multimedia Subsystem) using the **SIP** signaling protocol, rather than a separate circuit-switched path as in older generations.

---

## 3. The Access Network (RAN) and the generations

The **Radio Access Network** is the most visible and most capital-intensive layer: the cell sites, antennas, and radios that bridge the wireless device to the wired network.

### 3.1 The mobile generations

| Gen | Era | Core idea | Hallmark |
|---|---|---|---|
| 1G | 1980s | Analog voice | Car phones |
| 2G (GSM) | 1990s | Digital voice + SMS; SIM card introduced | Texting, prepaid |
| 3G (UMTS) | 2000s | Mobile data | Mobile internet |
| 4G (LTE) | 2010s | All-IP, fast broadband | Streaming, apps |
| 5G (NR) | 2019– | High speed, low latency, massive IoT | Slicing, FWA, private nets |
| 6G | ~2030 (research) | AI-native, terahertz, integrated sensing | Early experiments only |

5G is defined by three usage profiles: **eMBB** (enhanced mobile broadband), **URLLC** (ultra-reliable low-latency, for automation/robotics), and **mMTC** (massive machine-type communication, for IoT at scale).

### 3.2 Network elements and the radio chain

The base station is the **eNodeB** in 4G and the **gNodeB** (gNB) in 5G. The chain runs antenna → **radio unit (RU)** → **distributed unit (DU)** → **centralized unit (CU)** → transport to the core. Key engineering concepts: **MIMO/massive MIMO** (many antenna elements for capacity), **beamforming** (steering signal toward users), **carrier aggregation** (bonding spectrum blocks), and **small cells** (densification in high-traffic areas).

### 3.3 Standalone vs Non-Standalone, and Open RAN

- **NSA vs SA:** early 5G ran **Non-Standalone** — 5G radio anchored on a 4G core. **Standalone (SA)** uses a true 5G core and unlocks slicing, VoNR, and low-latency paths. As of 2026, SA is live in dozens of markets but adoption is uneven (Opensignal observed SA detection around the low-20s percent in South Korea and Spain versus single digits in much of Europe), and the industry's stated challenge has shifted from launching SA to *monetizing* it.
- **Open RAN (O-RAN):** disaggregates the RU/DU/CU and opens the interfaces between them so operators can mix vendors, add a **RIC** (RAN Intelligent Controller) for programmable optimization, and avoid lock-in. In 2026 it moved from pilots to commercial scale: AT&T is migrating most of its traffic onto open-capable platforms under a large Ericsson deal, Dish built a greenfield cloud-native network on Open RAN covering most of the U.S. population, Rakuten runs a multi-vendor network, and Vodafone is rolling out thousands of European sites. The performance gap to traditional RAN has narrowed to roughly single digits, though total cost of ownership is still modestly higher — the justification is strategic (vendor independence, security, innovation velocity), reinforced by Western policy pressure to reduce reliance on specific equipment vendors.

---

## 4. Transport: fronthaul, backhaul, and the core network of fiber

Radios are useless without the wired network that carries their traffic. **Transport** spans **fronthaul** (RU↔DU, extremely latency-sensitive), **backhaul** (cell site → core, via fiber or microwave), **metro**, and **long-haul core transport**. The physical media are overwhelmingly **optical fiber**, supplemented by **microwave** point-to-point links where fiber is impractical and **submarine cables** for intercontinental traffic. Technologies layered on fiber include DWDM (wavelength multiplexing), IP/MPLS and segment routing for packet transport, and increasingly software-defined, programmable transport. Transport is where latency budgets are won or lost, and it is a major slice of operator capital expenditure.

---

## 5. The Core Network

The **core** is the brain: it manages mobility, sessions, policy, and the subscriber database. The architecture changed shape between 4G and 5G.

### 5.1 4G Evolved Packet Core (EPC)

| Element | Role |
|---|---|
| MME | Mobility & session control (the control-plane anchor) |
| S-GW | Serving gateway (user-plane within the network) |
| P-GW | Packet gateway (to the internet; IP allocation, policy enforcement) |
| HSS | Home Subscriber Server (the master subscriber/credentials database) |
| PCRF | Policy and Charging Rules Function |

### 5.2 5G Core (5GC) — Service-Based Architecture

5G rebuilt the core as cloud-native software functions that talk over web-style APIs (HTTP/2 + JSON), making it modular and programmable. Principal functions:

| Function | Role |
|---|---|
| AMF | Access & Mobility Management (registration, connection) |
| SMF | Session Management (sets up PDU sessions) |
| UPF | User Plane Function (forwards the actual packets; can sit at the edge) |
| AUSF | Authentication Server Function |
| UDM / UDR | Unified Data Management / Repository (the subscriber data) |
| PCF | Policy Control Function (QoS, quotas, rules) |
| NRF | Network Repository (service discovery between functions) |
| NSSF | Network Slice Selection Function |
| NEF | Network Exposure Function (safely exposes network capabilities to outside apps) |

Two consequences matter commercially. **Control/user-plane separation (CUPS)** lets the UPF be pushed to the network edge for low latency (the basis of edge computing partnerships with hyperscalers). And **network slicing** lets one physical network present multiple virtual networks with different guarantees — a premium slice for an enterprise, a low-power slice for IoT — which is central to the 5G enterprise monetization story.

### 5.3 Voice: the IMS

Voice and messaging run over the **IMS**, a SIP-based subsystem common to fixed and mobile, delivering VoLTE/VoNR, VoWiFi, and RCS messaging. It is why "voice" is now just another data application rather than a separate network.

---

## 6. Identity and the data of telecom

If adtech's central problem is identity resolution, telecom's identity layer is far more deterministic — it is rooted in cryptographic credentials on a physical or embedded chip.

| Identifier | What it names | Notes |
|---|---|---|
| **IMSI** | The subscriber (SIM) | Globally unique; in 5G it is the **SUPI**, and it is sent encrypted as the **SUCI** to prevent IMSI-catcher tracking |
| **IMEI** | The device hardware | Used for stolen-device blocklists (EIR) |
| **MSISDN** | The phone number | What others dial; portable between operators |
| **ICCID** | The SIM card itself | Printed on the card |
| **eSIM / eUICC** | Embedded, reprogrammable SIM | Enables remote provisioning, multi-profile devices, IoT at scale |
| **TMSI / GUTI** | Temporary identities | Assigned over the air so the permanent ID isn't constantly broadcast |
| **IP address** | The session | Assigned per data session |

The **SIM/eSIM** is the trust anchor of the whole system: it holds the secret key that proves the subscriber is genuine and enables **mutual authentication** between device and network. **eSIM** is reshaping distribution (no physical card to ship), device design, and IoT logistics, and it underpins **roaming** — the mechanism by which your home operator's credentials are honored on a visited operator's network, settled later through clearing houses.

---

## 7. Signaling and protocols

The "schemas" of telecom are its signaling protocols — the standardized languages that let elements (and operators) interoperate.

- **SS7** — legacy control signaling for 2G/3G (call setup, SMS, roaming); still present and a known security weak point.
- **Diameter** — the 4G replacement for SS7-era authentication, authorization, and charging signaling.
- **GTP** — GPRS Tunneling Protocol; carries user-plane traffic through tunnels in the mobile core.
- **HTTP/2 + JSON (SBA)** — the 5G core's web-style service interfaces.
- **SIP** — session setup for IMS voice/video.
- **PFCP** — control-to-user-plane signaling under CUPS.
- **GTP-U / IPsec, NAS, RRC** — user-plane tunneling, non-access-stratum (device↔core) signaling, and radio resource control (device↔RAN).

Interoperability is governed by **3GPP** standards (organized into "Releases"; 5G spans Rel-15 onward, with **5G-Advanced** around Rel-18/19 and 6G targeted around Rel-21).

---

## 8. Spectrum: the scarce, licensed raw material

Radio spectrum is the irreplaceable input of wireless, and it is allocated by governments — usually by auction. Its physics drive network economics:

- **Low-band (<1 GHz):** travels far and penetrates buildings → wide coverage, lower capacity. Good for rural and indoor.
- **Mid-band (1–6 GHz, incl. **C-band**):** the workhorse balance of coverage and capacity; the main battleground of recent auctions.
- **mmWave (24 GHz+):** enormous capacity, very short range → stadiums, dense urban hotspots.

Licensing models include **exclusive licensed** (auctioned, the norm for mobile), **unlicensed** (Wi-Fi), and **shared/dynamic** schemes (e.g., CBRS in the U.S.), which lower the barrier to **private networks**. Spectrum is simultaneously an asset on the balance sheet, a regulatory instrument, and a strategic moat — and increasingly a contested resource as satellite direct-to-device players seek access to it.

---

## 9. The actors and market structure

The telecom value chain has distinct roles, analogous to a supply/demand split but organized around who owns the network versus who sells the service.

- **Mobile Network Operators (MNOs):** own spectrum and network (e.g., the major national carriers). The capital-heavy core of the industry.
- **MVNOs / MVNEs / MVNAs:** Mobile Virtual Network Operators resell capacity bought wholesale from MNOs (no spectrum of their own); enablers (MVNE) and aggregators (MVNA) provide the platforms behind them.
- **Equipment vendors:** Ericsson, Nokia, Samsung, Huawei, ZTE (RAN/core); plus the **chipset** layer (Qualcomm, MediaTek) and merchant silicon for Open RAN.
- **Tower companies / InfraCos / neutral hosts:** own and lease the physical sites (American Tower, Cellnex, etc.); a structural separation of "passive infrastructure" from "active network" that lets operators turn capex into opex.
- **Wholesale, interconnect, and roaming:** carriers, IXPs (internet exchange points), peering/transit relationships, submarine-cable consortia, and roaming clearing houses that settle cross-operator traffic.
- **Hyperscalers:** AWS/Azure/Google increasingly host core and Open RAN workloads and provide edge compute — both partner and potential disruptor.
- **Satellite / NTN players:** non-terrestrial networks (see §12) extending or competing with terrestrial coverage.

---

## 10. OSS/BSS: the operational and business backbone

This is the data-and-software layer that turns a network into a business — the closest analog to adtech's DMP/CDP/measurement stack, and where a large share of telecom "data" actually lives.

- **OSS (Operations Support Systems):** the network-facing systems — **fulfillment** (service activation/provisioning), **assurance** (fault and performance monitoring, SLA management), **inventory** (what assets exist where), and **orchestration** (increasingly automated, increasingly AI-assisted).
- **BSS (Business Support Systems):** the customer-facing systems — **CRM**, **order management**, **product catalog**, **mediation** (collecting and normalizing usage records), **charging**, **billing**, **revenue management**, and **partner settlement**.
- **Charging and CDRs:** usage is captured as **Call/Charging Detail Records**, then rated and billed. **Offline charging** bills after the fact (postpaid); **online charging (OCS)** authorizes in real time and is essential for **prepaid** and for enforcing quotas/throttling. The mediation→rating→billing pipeline is the financial heartbeat of the operator.
- **The data problem:** networks generate vast telemetry, but — as operators emphasized at MWC 2026 — automation and AI need *curated, high-quality* network data, not just more of it. Standardized data and AI-ready architectures are now a prerequisite for the self-optimizing networks vendors are demonstrating.

---

## 11. Services, products, and segments

What operators actually sell, beyond consumer mobile plans:

- **Consumer mobile** — prepaid/postpaid voice, messaging, data; bundles and family plans.
- **Fixed broadband** — delivered via **FTTH/FTTx** (fiber, using GPON/XGS-PON), **DOCSIS** (cable), **DSL/VDSL** (copper, declining), and satellite.
- **Fixed Wireless Access (FWA)** — home broadband over 5G; a major recent growth area, especially where fiber is uneconomic.
- **Enterprise & B2B** — connectivity, SD-WAN, managed services, security, cloud connectivity.
- **Private networks** — dedicated 4G/5G for factories, ports, campuses, mines; a flagship 5G-SA and Open-RAN use case.
- **IoT / M2M** — connectivity management for fleets of devices, often on eSIM and low-power profiles (RedCap, NB-IoT, LTE-M).
- **Wholesale & MVNO enablement** — selling capacity and platforms to other providers.
- **Convergence** — bundling mobile + fixed + content ("quad play") to reduce churn, a central retention strategy in mature markets.

---

## 12. Regulation, standards, and governance

Telecom is among the most regulated industries, because it controls scarce public spectrum and critical infrastructure.

- **Standards & coordination:** **ITU** (global spectrum coordination and the "IMT" requirements that define each generation), **3GPP** (the technical specifications), and the **GSMA** (the operator industry body).
- **National regulators:** allocate spectrum (auctions), set competition policy, manage **numbering and number portability**, and enforce consumer protections (e.g., FCC in the U.S., Ofcom in the UK, the BEREC framework in the EU).
- **Universal service / digital divide:** subsidies and obligations to extend coverage to rural and underserved areas.
- **Net neutrality:** rules (varying by jurisdiction and over time) on whether operators may prioritize or throttle particular traffic.
- **Lawful intercept & data retention:** legal obligations to enable authorized surveillance and retain certain records.
- **Security & supply chain:** restrictions on specific equipment vendors in several Western markets, a key driver of Open RAN and vendor-diversity policy.
- **Privacy:** subscriber and location data are highly sensitive and governed by both telecom-specific rules and general data-protection law.

---

## 13. The 2026 state of play and the road ahead

A snapshot of where the industry's attention sits, and where it is heading. *(These are fast-moving items reflecting early-to-mid 2026; treat specifics as a dated snapshot worth re-verifying.)*

- **5G monetization, not deployment, is the question.** Networks are largely built; the GSMA and operators frame the priority as turning SA capability into revenue via enterprise digitalization, private networks, slicing, speed-based tariffs, and FWA. Capital intensity remains high (major U.S. operators are still guiding to mid-teens-billion annual capex).
- **Open RAN at commercial scale.** It is no longer a pilot — but it is demanding on operator engineering teams, and the narratives of "scaling fast" and "still hard" are both true. Vendor consolidation around RIC/automation (e.g., Nokia absorbing Juniper's RIC/SMO assets) is underway.
- **AI moving into the live network.** The clearest MWC 2026 theme: AI shifting from *monitoring* to *actively controlling* networks — agentic optimization of RAN, traffic, and fault management — contingent on the network architecture and data being ready, which most operators concede they are not yet.
- **Satellite direct-to-device (NTN).** Space-based cellular to *unmodified* phones became real: AST SpaceMobile secured U.S. regulatory authorization for commercial service and is scaling its constellation toward commercial activation, while SpaceX/Starlink pursues the same direct-to-device market. This raises live questions about spectrum, neutral-host economics, and regulatory oversight, and reframes "coverage" as a hybrid terrestrial-plus-space problem.
- **Fiber and convergence** continue as the fixed-side growth engine, with FWA filling gaps.
- **6G on the horizon (~2030).** Still early research — terahertz spectrum, AI-native architecture, integrated communication-and-sensing — with standardization targeted around the end of the decade.

---

## 14. Quick Reference: domains at a glance

| Domain | What it does | Key elements / data | Central tension |
|---|---|---|---|
| **Access (RAN)** | Wireless bridge to device | gNodeB, RU/DU/CU, RIC, antennas | Coverage vs capacity vs cost; vendor lock-in |
| **Transport** | Carries traffic to core | Fiber, microwave, DWDM, submarine cable | Latency budget & capex |
| **Core network** | Mobility, sessions, policy | AMF/SMF/UPF, EPC, slicing, CUPS | Cloud-native flexibility vs reliability |
| **Voice (IMS)** | Voice/messaging as IP | SIP, VoLTE/VoNR, RCS | Legacy migration |
| **Identity** | Who/what is connecting | IMSI/SUPI, IMEI, MSISDN, SIM/eSIM | Security & privacy of identifiers |
| **Signaling** | Inter-element/operator language | SS7, Diameter, GTP, SBA, SIP | Interoperability vs legacy security |
| **Spectrum** | The wireless raw material | Low/mid/mmWave; licensed/shared | Scarcity, cost, allocation |
| **Actors** | Who owns vs sells | MNO, MVNO, vendors, towercos, hyperscalers | Capex burden & disaggregation |
| **OSS/BSS** | Run & monetize the network | Provisioning, CDRs, charging, billing | Data quality for automation |
| **Services** | What's sold | Mobile, FWA, fiber, private nets, IoT | Differentiation & churn |
| **Regulation** | The rules of the road | 3GPP/ITU/GSMA, spectrum, numbering, security | Public interest vs operator economics |

---

### A note on scope
This study is deliberately structural — it maps *what the network is made of, how traffic and money flow through it, and who the players are*. It can go deeper in several directions depending on your goal: a protocol-and-signaling deep-dive (the "schemas"), a 5G-core/Open-RAN architecture walkthrough, an OSS/BSS and charging data-model treatment, a market/competitive map of specific operators and vendors, or a regulatory/spectrum-policy analysis. Tell me which and I can expand that section.
