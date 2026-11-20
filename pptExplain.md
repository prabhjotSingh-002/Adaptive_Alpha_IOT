# AdaptiveAlpha IoT — PPT explanation and viva notes

Source: `AdaptiveAlpha_IoT_Final_Merged_13_Slide_Internal_Evaluation.pptx.pdf` (13 pages). Yeh uploaded presentation ka explanation hai. Figures ko naye experimental results mat samajhna. Slides 10–12 ke embedded charts visually inspect kiye gaye hain. Project ke current results aur presentation ke historical snapshots alag ho sakte hain.

## Slide 1 — Title and project identity

**Deadline-Constrained Energy-Aware Secure Data Delivery in RPL-Based IoT Networks** ka matlab: sensors ka data security maintain karte hue deliver karna, queue mein maximum waiting bound rakhna, aur energy cost ko decision mein consider karna.

- **IoT:** Internet of Things; chhote connected devices jo readings generate karte hain.
- **RPL:** low-power/lossy IPv6 networks ka routing protocol. Existing routes reuse hote hain; project naya routing protocol propose nahi karta.
- **Deadline-constrained:** reading ko indefinitely batch mein hold nahi kar sakte. Queue deadline aur complete network delivery deadline alag hain.
- **Energy-aware:** energy model/costs se informed selection; title khud measured energy saving prove nahi karta.
- **Secure delivery:** confidentiality, integrity aur authentication ke saath root acceptance.
- **Application layer:** protection reading/packet par lagti hai, routing stack ke upar.
- **Contiki-NG:** constrained-device firmware environment. **Cooja:** simulation environment.
- **Research prototype:** experimental system; production key provisioning aur physical deployment validation complete hone ka claim nahi.

Presented-by names/roll numbers aur supervisor academic attribution hain. “DTU LOGO” placeholder actual logo asset ki jagah dikh raha hai.

**Bolne ke liye:** “Hum sensor-to-root secure delivery mein cipher aur local batching ko jointly choose karne ka framework study kar rahe hain. Goal useful authenticated delivery ki energy cost kam karna hai, delivery aur delay constraints ke saath.”

## Slide 2 — Contents / roadmap

Presentation ka flow problem → design → implementation → evaluation → outcomes hai. Slides 3–5 motivation, objectives aur foundations; 6–8 architecture/security/policy; 9–10 methodology/metrics; 11–12 results aur limitations; 13 closing.

**Research foundation** existing standards/tools ka basis hai. **Methodology** batati hai experiment kaise fair hoga. **Results** executed evidence hain. **Future scope** abhi pending validation hai. Slide 12 mein discussion aur future work combined hain; separate conclusion slide nahi hai.

**Bolne ke liye:** “Pehle overhead ka problem explain karenge, phir packet aur policy design, aur finally available evidence aur uski limitations.”

## Slide 3 — Introduction, motivation and overhead diagram

**Low-power** nodes limited energy mein operate karte hain. **Lossy** links par packets drop ho sakte hain. **CPU** computation karta hai; **RAM** queue aur security state store karti hai. **Multi-hop** mein packet relays se root tak jaata hai. **Contention** mein multiple nodes same radio medium ke liye compete karte hain.

Energy CPU/MCU computation, encryption/authentication, radio transmission, listening aur relay forwarding mein lagti hai. **MCU** microcontroller hai. **TX** transmission hai. Listening bhi energy leta hai, chahe useful packet receive na ho.

Diagram mein H header, R1/R2/R3 individual readings aur TAG authentication tag hain. Har reading 10 bytes, header 11 bytes, tag 16 bytes:

- Separate packet: 11+10+16 = **37 B**. Three packets = **111 B**, three submissions.
- Batched packet: 11+3×10+16 = **57 B**, one submission.
- Saved envelope bytes: 54/111 ≈ **48.6%**; submissions reduction 2/3 ≈ **66.7%**.

Yeh application bytes hain. IPv6/UDP/MAC headers, retransmissions, forwarding aur radio listening is arithmetic mein included nahi. Isliye 48.6% bytes reduction ko 48.6% energy reduction nahi bolna.

**Temporal batching** same sensor ki readings ko time ke across combine karti hai. Routing relays doosre sensors ki plaintext readings merge nahi karte. Waiting ki wajah se latency badh sakti hai. **Confidentiality** content chhupati hai; **integrity** modification detect karti hai; **authenticity** permitted key context se origin validate karti hai. AEAD remove karne se comparison ki service badal jaati hai.

**Bolne ke liye:** “Batching repeated header/tag overhead share karti hai, lekin reading ko queue mein wait karna padta hai. Hum isi energy–delay trade-off ko security preserve karke study karte hain.”

## Slide 4 — Research problem, action and objective

Action **a=(AEAD profile, batch cap)** hai. Profile AES-CCM ya Ascon; cap maximum readings 1/2/4. Cap maximum hai, actual packet occupancy ki guarantee nahi.

**AEAD** authenticated encryption with associated data: encrypted payload ke saath visible metadata ko bhi authenticate kar sakte hain. Objective expected network energy / unique authenticated deliveries minimize karna hai. Numerator kam aur useful delivery denominator high hona desirable hai. Delivery collapse hone par sirf low total energy misleading ho sakti hai.

Constraints: confidentiality/authentication; bounded memory/packet size; queue hold deadline aur E2E delay; reliable delivery; decision/switching cost. **Optimization subject to constraints** ka matlab cheapest action tabhi acceptable hai jab bounds satisfy ho.

Five objectives: two standard AEADs integrate; bounded aggregation; joint policy; energy/delivery/latency/lifetime evaluation; static aur single-feature controls se comparison. **Contribution** framework/implementation/evaluation proposal hai, universal improvement claim nahi.

- **H1:** authenticated reading ki energy cost kam ho sakti hai.
- **H2:** acceptable service ke saath lifetime improve ho sakti hai.
- **H3:** joint selection ka benefit isolated cipher/batching selection se extra ho sakta hai.

Hypothesis test karni hai; negative result bhi valid outcome hai. **On-node bounded logic** fixed candidate count aur memory use ko refer karta hai.

**Bolne ke liye:** “Sirf cipher fast hona enough nahi; actual useful network delivery cost aur delay constraints saath evaluate karne hain.”

## Slide 5 — Literature and research gap

Table foundations map karti hai:

| Source | Meaning and project role |
|---|---|
| Contiki, Dunkels et al. 2004 | Lightweight event-driven sensor OS foundation; Contiki-NG us lineage ka modern environment hai. Event-driven matlab events/timers par execution. |
| Cooja, Österlind et al. 2006 | Network aur mote behavior study karne ka simulator; different abstraction levels possible. |
| RPL, RFC 6550, Winter et al. 2012 | Low-power/lossy IPv6 routing standard. RFC documented Internet specification hai. Existing objective function/routes reuse hote hain. |
| AES-CCM, NIST SP 800-38C | Standard authenticated-encryption mode; protected profile 1. |
| Ascon-AEAD128, NIST SP 800-232 | Standardized lightweight authenticated-encryption variant; protected profile 2. Exact standardized variant matters. |
| Software energy, Dunkels et al. 2007 | State-time accounting se energy estimate ki foundation; project Energest plus declared current model use karta hai. |

**NIST** standards institution; **SP** Special Publication. Literature routing, security, measurement aur experimentation enable karti hai. Project question in capabilities ko joint cipher+batch decision mein combine karna hai under energy/delay/reliability/memory/switching constraints.

Yeh slide exhaustive related-work survey ya “world mein kisi ne joint selection nahi kiya” ka proof nahi hai. **Research gap** ko precise relevant comparative literature ke saath establish karna hoga; foundational references alone novelty establish nahi karte.

**Bolne ke liye:** “Hum existing routing aur standardized cryptography reuse karte hain; project-specific work decision policy, bounded aggregation aur reproducible evaluation hai.”

## Slide 6 — Architecture and network model

Data path ke seven steps:

1. **Generate:** reading ID, value aur local creation timestamp. ID duplicates identify karne mein help karta hai.
2. **Buffer:** four-slot FIFO; first-in first-out. Count cap, oldest hold time aur byte fit flush control karte hain.
3. **Choose:** B3/B6/P1 profile/cap select karte hain.
4. **Protect:** AEAD seal reading bytes encrypt aur tag produce karta hai; UDP se submit.
5. **Network:** UDP → IPv6 → 6LoWPAN → MAC/radio, RPL routes ke through.
6. **Root:** allowed context, authentication, replay aur unique reading acceptance.
7. **Host:** logs parse, metrics calculate, manifests/plots/dashboard present.

**UDP** datagram transport; local submission guaranteed root delivery nahi. **IPv6** addressing/network layer. **6LoWPAN** constrained links ke liye IPv6 adaptation/compression. **MAC** medium access control. **Relay** forwarding node. **Root** destination/collection node 1.

Topology sketch 1 root +8 sensor/relay clients dikhata hai. Lines illustrative hain; actual RPL parents simulation logs se establish honge. Har client sensor aur relay dono ho sakta hai.

**Control inputs:** Energest state, residual-budget model aur calibrated costs. Actual current implementation mein configured rate aur static costs ki limitations hain; diagram ko full measured dynamic adaptation ka evidence nahi bolna.

**GEN** generation event; **TX2** structured protected transmission event; **RX2** receive/acceptance event. **Manifest** run identity/config/hashes/status record. Flask dashboard host-side viewer hai; mote policy controller nahi.

**Bolne ke liye:** “Decision node par hota hai; routers encrypted bytes forward karte hain aur root authenticate karke readings accept karta hai.”

## Slide 7 — Cryptographic design and packet format

Both profiles use 128-bit keys and 16-byte tags. AES-128 means key length 128 bits; CCM combines counter-mode encryption with authentication. Ascon-AEAD128 standardized AEAD construction hai. Lightweight label har workload par lower energy guarantee nahi.

**Nonce:** per-key encryption invocation ka unique input; AES profile 13 bytes, Ascon 16 bytes. Nonce secret hona necessary nahi, unique hona critical hai. **Key** secret context material. **Tag** integrity/authentication check. Same tag length packet-overhead fairness improve karti hai; identical algorithms/security proofs imply nahi karti.

Visible authenticated header fields:

| Field | Bytes | Purpose |
|---|---:|---|
| Version | 1 | Wire-format interpretation |
| Sender | 2 | Origin/context identity |
| Profile | 1 | AEAD selection |
| Epoch | 2 | Security-context generation identity |
| Counter | 4 | Nonce/replay sequence state |
| Count | 1 | Number of encoded readings |

Total 11 bytes. **AAD** associated authenticated data: header visible rehta hai, tamper detection mein bound hota hai. Reading payload encrypted hai. Packet size **27+10n**: n=1/2/3/4 ke liye 37/47/57/67 bytes. 67-byte budget mein four readings fit; 47-byte budget mein only two. Application budget radio frame ki total size nahi.

Root pipeline: permitted context → candidate replay-window check → AEAD/body verification → replay-state commit → deduplicate reading IDs. Candidate counter check authentication se pehle ho sakta hai, lekin accepted replay state successful verification ke baad hi mutate honi chahiye. Otherwise forged high counter legitimate traffic block kar sakta hai.

**Replay** old valid packet resend karna. **Dedupe** repeated reading ko double count hone se rokna. Dono different protections hain. Profile-specific keys/counters retain hon; switch back par previous counter resume kare, zero reset se nonce reuse risk hota hai. Fixed simulation test keys production provisioning nahi. **N0** unprotected diagnostic hai; protected failure par N0 fallback forbidden. Safe AES/cap1 fallback ab bhi protected hota hai.

**Bolne ke liye:** “Header readable hai lekin authenticated hai. Root plaintext reading tabhi release karta hai jab tag aur body valid hon; replay state bhi uske baad commit hoti hai.”

## Slide 8 — Aggregation timeline and adaptive policy

Timeline mein readings t=0,1,2 par aati hain. Oldest deadline t=3 par expire hoti hai. Existing queue R1–R3 pehle flush hoti hai; R4 uske baad offer hoti hai. Isliye configured cap4 ke saath actual batch3 possible hai. **Oldest-reading deadline** new arrival se reset nahi hoti. Diagram ideal timing contract hai; real service tick/processing timestamps se actual behavior verify karna hai.

“Every reading preserved” desired accounting behavior hai; full queue, network loss/depletion jaise cases mein explicit drop/undelivered accounting necessary hai. Is phrase ko unconditional delivery guarantee mat samajhna.

- **B3:** residual energy above 6 J par AES, below 3 J par Ascon; beech mein previous profile hold. **Hysteresis** threshold ke paas repeated toggling avoid karti hai. These are displayed configuration thresholds, universal cipher-efficiency facts nahi.
- **B6:** fixed calibrated cipher, largest feasible batch cap; batching-only ablation.
- **P1:** available action costs se joint profile/cap selection, dwell aur saving/transition checks ke saath.

Six candidates A1/A2/A4 and S1/S2/S4 mean AES/Ascon × cap1/2/4. Zero cost means missing measurement, free encryption nahi.

Decision flow: read inputs → packet/deadline/key feasibility → minimum available nJ/reading rank → dwell/savings check → apply/retain. **Dwell** minimum hold interval; **margin** required saving; **transition cost** profile/cap change ka accounted cost. Constraints should override holding an infeasible action. Missing data par AES/cap1 protected fallback.

**Wire proof:** POLICY decision log ko sealed TX2 profile aur authenticated RX2 profile ke saath correlate karo. A log saying “profile changed” alone actual transmission prove nahi karta. Current code rate configured period se derive karta hai; P1 residual energy directly rank nahi karti. In limitations ko explain karna zaroori hai.

**Bolne ke liye:** “Cap ek upper limit hai. Deadline aur packet fit actual occupancy decide karte hain; policy change ka proof transmission aur root acceptance tak trace karna hota hai.”

## Slide 9 — Experiment arms and setup

**Arm** experimental configuration; **baseline/control** reference comparison; **ablation** component isolate karna.

| Arm | Cipher | Batching | What comparison teaches |
|---|---|---|---|
| B1 | AES | cap1 | Protected reference |
| B2 | Ascon | cap1 | Same batching, alternative cipher |
| B3 | Energy threshold | cap1 | Cipher-selection mechanism |
| B4 | AES | cap4/deadline | Batching with fixed AES |
| B5 | Ascon | cap4/deadline | Batching with fixed Ascon |
| B6 | Calibration-selected fixed cipher | adaptive | Batching policy contribution |
| P1 | Cost-selected profile | adaptive | Joint-policy hypothesis |
| N0 | No AEAD | cap1 or4 | Diagnostic transport/aggregation only |

Displayed short setup: 8 clients+root; 1 s period; 24 readings/client, so **192 scheduled readings**; deadline3 s; app budget67 B; warm-up60 s; drain15 s; service tick125 ms. Warm-up routes establish karne ka interval; drain generation ke baad pending delivery time. Tick periodic servicing hai; exact microsecond deadline guarantee nahi.

Native Cooja functional behavior establish karta hai. Z1 emulation declared hardware-component model ke saath timing/energy estimation support karti hai. Physical battery accuracy separately validate hogi.

Pipeline config→build→Cooja→raw logs→parse→metrics→compare. **Source/config identity** stale/mixed build avoid karne mein help karti hai. Fairness: same reading schedule/IDs/workload; matched seeds; same target/model/source where required. Seed random scenario identity control karta hai, lekin seed alone matching traffic prove nahi karta.

**Calibration** choices/costs estimate karne ka dataset. **Held-out evaluation** separate seeds/data par testing, selection bias reduce karne ke liye. Statistical independent unit complete run/seed hai, 192 correlated readings ko 192 independent experiments nahi bolna. Slide explicitly says full matrix not executed.

**Bolne ke liye:** “Controls se cipher aur batching ke effects separate karte hain. Calibration ko final evaluation se alag freeze karte hain.”

## Slide 10 — Metrics, units, energy model and chart

### Reading PDR

**D_unique/G_expected:** unique delivered readings / specified expected generation denominator. Example48/48=100%; duplicate packet se numerator nahi badhega. One lost batched packet several readings lose kar sakta hai, isliye packet PDR aur reading PDR differ karte hain. Finite-budget analysis mein generated-vs-prospectively-scheduled denominator explicitly state karo.

### p95 end-to-end delay

Each accepted reading delay = global RX timestamp − global GEN timestamp. Global simulator time different mote clocks ke offset se bachata hai. **p95** 95th percentile: observed delivered-reading delays ka approximately95% is value se at/below hota hai, percentile method ke according. Yeh “95% generated readings delivered within deadline” imply nahi karta; lost readings delays mein absent hain. PDR saath report karo. End-to-end delay includes queue wait plus processing/network delivery.

### Energy per authenticated reading

Sum battery-node energy / unique authenticated deliveries. Root excluded under stated powered-root assumption. Zero deliveries par ratio undefined hai, zero energy cost nahi. Units: **J** joule; **mJ**=10^-3J; **nJ**=10^-9J; 1mJ=1,000,000nJ. 247.2mJ≈247,200,000nJ.

### State-time model

**E=V×Σ(I_state×T_state)**. V voltage; I current; T seconds; ampere×volt×second=joule. Example3V×0.001A×1s=0.003J=3mJ. **Energest** duration counters record karta hai; declared component currents se estimated energy nikalti hai. CPU active vs LPM low-power states; radio TX vs LISTEN receive/listen states. MCU aur radio simultaneous active ho sakte hain; valid component accounting use karo. Crypto CPU work already CPU time mein ho to separate crypto energy add karna double count hoga.

Slide Z1 model3V, MSP4308MHz, CC2420 radio specify karti hai. MHz clock frequency hai, energy value nahi. Modelled energy actual battery measurement nahi.

### Lifetime

**FND:** first battery-node death. **HND:** at least half population depleted. Two nodes mein first death hi half hai, so HND=FND possible without both dying. **Functional lifetime:** configured service threshold persistent failure. Crossing aur confirmation time different hain. **Censored:** simulation horizon tak event observe nahi hua; horizon par death assume nahi karte.

### Embedded chart

X-axis modes N0-single/N0-batch/B1–B6/P1; Y-axis energy per delivered authenticated reading in mJ, lower potentially better only with comparable delivery/service. Dashed horizontal line B1 reference; black whiskers displayed95% bootstrap CI. N0 missing comparable modelled energy ko zero-consumption mat samajhna. Bar labels n loaded run count hain.

**Bootstrap CI:** run-level values resample karke uncertainty interval estimate. Mixed cohorts ka systematic bias CI repair nahi karta. **Pseudo-replication** correlated within-run readings ko independent runs treat karna hai. Screenshot historical mixed-run view hai, admitted final comparison nahi.

**Bolne ke liye:** “Energy ko delivered authenticated readings se normalize karte hain, aur PDR/latency saath read karte hain. Model uncertainty aur independent runs ki uncertainty dono matter karte hain.”

## Slide 11 — Delivery and aggregation results; every chart explained

This main table is **native**, root+2 clients, one paired seed,48 readings/arm. Slide9 ka8-client setup aur right-hand historical screenshot alag context hain.

B1/B2:48 authenticated /48 generated;48 UDP submissions;1,776 app bytes; p95≈43.8ms; batch1. Arithmetic48×37=1776.

B4/B5:48/48;16 submissions;912 app bytes; p95≈3039.8ms; actual batch3. Arithmetic16×57=912 and16×3=48. Cap4 despite batch3 follows deadline-first timeline.

### Bottom-left communication chart

Light bar cap1, green cap4. UDP submissions48→16 gives(48−16)/48×100=**66.7% reduction**. Bytes1776→912 gives864/1776×100≈**48.6% reduction**. These are application submissions/bytes; radio frames/retries/energy require separate measurement. Same48/48 delivery makes this pilot's overhead trade-off meaningful.

### Bottom-right latency chart

Cap1≈43.8ms, cap4≈3039.8ms. Difference3039.8−43.8=**2996ms**. Most added delay queue waiting se consistent hai. Three-second local hold limit plus transport delay means E2E can exceed3s. Cap4 lower transmissions ke saath higher tail delay dikhata hai.

### Top-right historical screenshot

Two panels: reading PDR (higher generally better) and p95 delay in ms (lower generally better). Mode colors categories represent karte hain, severity scale nahi. Error bars displayed bootstrap uncertainty hain. PDR Y-axis approximately0.90–1.00 se truncated hai; bar heights ko zero-based percentage differences jaisa interpret mat karo. Some mode PDRs below1 dikhte hain. Batching delay bars near3s hain. Exact tiny screenshot values available table/raw results ke bina quote mat karo.

Screenshot8-client historical cohort ka hai. Isko left48-reading pilot ke confidence intervals, matching repetitions ya same-run evidence ke roop mein combine nahi karna.

**Bolne ke liye:** “Is small functional pilot mein same protected delivery ke saath submissions roughly two-thirds aur application bytes roughly half kam hue, lekin p95 roughly3seconds badha. Yeh energy saving measurement nahi hai.”

## Slide 12 — Historical energy/policy discussion; every chart explained

Top labels clearly historical8-client view, modelled energy, unequal run counts aur unqualified P1 result kehte hain.

### Left energy chart

X modes, Y mJ per authenticated delivered reading; dashed B1 reference; whiskers95% bootstrap CI as displayed. B4/B5 bars B1 se slightly lower, B3/B6/P1 slightly higher dikh rahe hain. Visual ranking alone causal policy benefit prove nahi karti because cohorts unequal/mixed hain. N0 missing modelled/authenticated comparable value ko free operation nahi bolna.

Bottom table: B1 n12,247.2mJ; B4 n10,243.9mJ; P1 n5,254.6mJ. Table arithmetic B4 vsB1≈1.33% lower, P1 vsB1≈2.99% higher hai. Yeh **descriptive displayed differences** hain; qualified improvement/degradation estimates nahi.

**Visible consistency issue:** embedded energy graph ke tiny n labels B1≈5/B4≈4 jaise dikhte hain, jabki table12/10 kehta hai. Underlying same selected run set verify kiye bina graph/table ko one coherent cohort mat bolo. Screenshot ke exact small labels readable original data se confirm hone chahiye. Presentation refresh par consistent cohort/manifest references attach karo.

### Policy-switch chart (middle/right panel ka left subchart)

X B3/B6/P1; Y mean switches per run. B3≈8, B6≈0, P1≈8 displayed hain. Eight clients mein startup assignments count hone par8 aa sakta hai; this is a possible explanation, established trace result nahi. “Eight switches” se eight secure profile transitions prove nahi hote. Match per-node old/new POLICY, TX2 and RX2.

Zero switches alone failure nahi: stationary optimal action unchanged reh sakta hai. Conversely fallback bhi zero changes de sakta hai. Reason codes/calibration identify karenge.

### Cipher-profiles-used chart (rightmost subchart)

Y run count, X B3/B6/P1; legend blue AES used, orange Ascon used. Displayed blue counts approximately3/5/5, orange bars absent hain. Means screenshot's reported profile-use data AES indicate karti hai; guaranteed actual wire profile ka conclusion audit ke bina nahi. A run could theoretically use both profiles, so profile-use counts mutually exclusive categories necessary nahi.

B6 expected configured/calibrated profile ke saath displayed AES-only usage ko trace karna chahiye; possible historical logging/config inconsistency ko confirmed cipher behavior mat bolo.

### Meaning of limitations and future scope

Historical P1 costs unavailable the, so AES/cap1 safe fallback dominated. Joint-policy benefit is screenshot se unproven. Newer audited Z1 smoke exists, so “historical unavailable” ko current universal statement mat banao.

Next: decision→sealed packet→verified receive validate; calibration freeze; held-out paired comparisons; PDR/p95 with energy; finite-budget lifetime. **Finite budget** explicitly limited modelled battery energy hai. Unbounded budgets death/switch-threshold lifetime evidence nahi de sakte.

**Bolne ke liye:** “Yeh historical dashboard discussion hai. Unequal mixed cohorts aur earlier fallback ke kaaran P1 advantage claim nahi kar rahe. Next acceptance target wire-level policy verification aur paired held-out evaluation hai.”

## Slide 13 — Closing and questions

Thank-you slide title, contributors aur supervisor repeat karti hai. Closing mein project ka tested scope accurately bolo: secure framework, bounded batching aur available functional evidence; full calibrated joint-policy/lifetime validation pending acceptance ke saath explain karo.

**Suggested closing:** “Humne secure application delivery aur bounded batching ka framework build kiya. Available pilot communication-overhead aur delay trade-off dikhata hai. Joint adaptive energy benefit establish karne ke liye qualified calibration, matched comparisons aur finite-budget validation complete karna hai.”

## Viva quick answers and common confusions

| Examiner ka question | Reasoned answer |
|---|---|
| Cap4 par3 readings kyun? | Oldest deadline fourth arrival se pehle service hoti hai; cap upper bound hai. |
| Bytes half toh battery double? | Energy radio listening/CPU/forwarding/retries par bhi depend karti hai; direct conversion valid nahi. |
| Ascon always better? | Implementation, target, payload aur network overhead se ranking change ho sakti hai; measure karna hai. |
| RPL mein change? | Existing routing reuse; novelty application-layer decision/measurement work mein study ho rahi hai. |
| Tag encryption hai? | Tag authenticity/integrity verify karta hai; confidentiality payload encryption deta hai. |
| AAD public kyun? | Routing/context interpretation ke liye visible metadata ho sakta hai; authentication tampering detect karti hai. |
| Nonce reset allowed? | Same key ke under reuse avoid karna essential; safe epoch/counter persistence/reset policy chahiye. |
| PDR100% means real deployment guarantee? | Particular pilot outcome hai; broader conditions/independent repetitions chahiye. |
| p95<5s means all readings delivered? | Delivered samples ka delay statistic hai; missing readings PDR/service metrics mein dikhengi. |
| Security fallback kya? | AES/cap1 protected fallback; N0 prohibited fallback hai. |
| HND=FND means both nodes dead? | Two-node population mein first death half population hai; both dead necessary nahi. |
| Why seven protected arms? | Static cipher, static batching, cipher-only, batching-only aur joint effects separate karne ke liye. |
| More readings means larger statistical n? | Independent experimental unit run/seed hai; readings within same network correlated hain. |
| Can bootstrap fix mixed results? | Resampling uncertainty estimate karta hai; incompatible cohorts ko scientifically comparable nahi banata. |
| Switching log enough? | Actual sealed TX2 aur authenticated RX2 profile/counter evidence bhi chahiye. |

## Presentation corrections to remember

1. Slide11 main2-client pilot aur8-client screenshot clearly distinguish karo.
2. Slide12 graph/table n mismatch reconcile kiye bina pooled conclusion mat do.
3. Historical fallback labels ko newer smoke results par automatically apply mat karo.
4. “Every reading preserved”, “adaptive” aur “qualified” ko actual checks ke scope mein explain karo; guaranteed delivery/full runtime learning imply nahi.
5. Current code review mein fresh suite98 tests/4 failures recorded hai; invalid deadline-test ABI/budget harness diagnose hua. Tests green hone ka stale claim mat karo. See `finalPLAN2X.md` Section15 and `phase_jouney/final2x_phase_01.md` for the audit checkpoint.
6. This explanation did not execute new simulations or revalidate every numeric slide claim against raw logs. Arithmetic and displayed chart interpretation checked hain; final experimental claims ko exact manifests/cohorts se link karna baaki hai.
