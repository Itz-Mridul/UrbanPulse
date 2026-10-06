# CascadeIQ — Judge Q&A Preparation
## Indradhanu PCCOE 2026 — Disaster Resilience Domain

> Rehearse this as a mock panel. All answers should be conversational, not read.
> Key principle: **lead with scope honesty, then strength**. Judges trust teams that know their limits.

---

## Category A: Problem & Originality

**Q1: What problem does CascadeIQ solve?**
> Indian disaster agencies already forecast individual hazards well. CascadeIQ solves the integration gap — the system that connects "heavy rain is coming" to "a community 45km downstream should evacuate now." Without that connector, a local flood-warning system watching local rainfall can be blindsided by a flash flood from a landslide-dam burst upstream it never knew about.

**Q2: How is this different from IMD/CWC/NDMA systems?**
> CascadeIQ is not a competing forecast — it is a consumer of their forecasts. IMD gives us rainfall. GSI gives us landslide susceptibility maps. CWC gives us river gauge data. CascadeIQ ingests all three and asks: "What is the probability that these independent hazards combine into a cascade?" That question is not currently answered by any single system.

**Q3: Why Bayesian Networks specifically? Why not a deep learning model?**
> Three reasons: (1) we have very few labelled multi-hazard cascade events — Bayesian Networks work well with small data. (2) Bayesian Networks give us an explicit causal graph — every alert shows the probability of each node in the cascade, which is the explainability requirement for authority trust. (3) The causal structure is physics-defined, not learned, so we never risk the network learning spurious correlations from limited training data.

**Q4: What is the research gap you're addressing?**
> In a review of 324 AI-based multi-hazard early warning papers, only 4 modelled hazards as causal chains rather than independent events. 55% focused on hazard forecasting; only 1% on response preparedness. CascadeIQ sits in that 1%.

---

## Category B: Technical Depth

**Q5: Walk me through the inference pipeline.**
> Input sensor readings enter the physics module first. Caine (1980) checks whether rainfall intensity-duration exceeds the Himalayan landslide trigger threshold for the observed slope angle. Korup (2002) checks whether estimated debris volume is large enough to block the channel width. These outputs — as plausibility scores — multiply into the Bayesian Network's prior CPDs. The BN then runs Variable Elimination to compute P(DownstreamFlood | observations). That probability, plus the physics-estimated flood travel time, feeds the Impact Layer and Action Engine.

**Q6: How did you calibrate the Bayesian Network CPDs?**
> For the MVP we use physics-informed priors from the published literature. The Caine threshold gives us the rainfall → landslide CPD; the Korup ratio gives us the debris → blockage CPD; empirical GLOF studies give us the blockage → flood CPD. In a production system we would update these CPDs using EM (Expectation-Maximization) on the historical event database.

**Q7: How do you compute the flood travel time?**
> Using the kinematic wave approximation from Huss et al. (2007): travel time ≈ valley length / (Manning's equation flow velocity). For Sikkim — Teesta Valley (45km, slope 32°, channel width 120m) this gives 3.2–5.8 hours. This is the window we use to size evacuation lead time.

**Q8: What is the Impact Score?**
> Impact Score (0–100) = 100 × P(flood) × (Exposure × 0.6 + Vulnerability × 0.4). Exposure is normalized from OSM-queried population, hospitals, roads. Vulnerability is the inverse of shelter coverage — a community with no emergency shelters near the flood zone scores higher vulnerability.

**Q9: What does "physics-constrained" mean exactly?**
> It means the causal DAG structure of the Bayesian Network was designed by physics, not learned. The edge Rainfall → Landslide exists because geophysics says rainfall causes soil saturation which reduces shear strength. The AI never invents a causal relationship it was never shown. Only the conditional probability distributions within that physics-defined structure are calibrated from data.

---

## Category C: Validation & Honesty

**Q10: How do you know this would have actually worked for Sikkim 2023?**
> We show it in the Historical Replay tab. Using the pre-event data reported in Sattar et al. (2024), we feed the reconstructed sensor readings step by step. The system raises ORANGE at T-24h and RED at T-12h. The confirmed flood event arrives at T=0. That gives a 12-hour verified alert window, with a 3–6h flood wave arrival estimate meaning ~6–9h for downstream communities to act.

**Q11: Is this real data or simulated?**
> Honest answer: the replay data is a synthetic reconstruction from published research values — labeled SYNTHETIC_HISTORICAL throughout the system. The physics equations are calibrated to real published thresholds. The scenario matches the confirmed event timeline. We never call it real sensor data — the label is always visible.

**Q12: What is the false alarm rate?**
> We don't have a real operational dataset to calculate precision/recall. In the backtest, the system correctly stays GREEN at T-72h (no false alarm) and escalates gradually. In a production system you would track confirmed vs. unconfirmed alerts over time and tune tier thresholds accordingly — which is why the human-in-the-loop verification step exists.

**Q13: Can this work outside Sikkim?**
> The physics equations are general — they use terrain inputs (slope, channel width, valley length) that can be parameterized for any Himalayan catchment. The Bayesian Network structure is the same. The region-specific pieces are: DEM for terrain analysis, historical event labels for CPD calibration, and OSM/population data for the impact layer. Extending to a new region requires those three inputs.

---

## Category D: Ethics & Safety

**Q14: What if the system issues a false RED alert causing unnecessary evacuation?**
> This is exactly why human-in-the-loop is a core design requirement, not a checkbox. No alert reaches "public" status without an authority officer reviewing and clicking Verify. The system can raise RED internally, but the authority has full discretion to downgrade or dismiss. The recommended action panel shows the specific towns, highways, and shelters involved — so the officer can sanity-check against ground truth before committing.

**Q15: How do you handle model uncertainty?**
> Three ways: (1) The causal path shows individual node probabilities — an officer can see that the flood probability is high but the blockage probability is only 45%, indicating uncertainty in that step. (2) We show a time lag range, not a single number — explicitly communicating estimate uncertainty. (3) Alerts escalate through tiers — the authority officer at YELLOW has more time to gather additional information before RED is issued.

**Q16: What about communities that don't have smartphones or internet?**
> CascadeIQ is an authority-side tool — it connects to SDMA/NDMA control rooms, not directly to communities. The last mile (SMS, sirens, community mobilisation) is handled by existing infrastructure. We specifically do not claim to solve Wayanad-type warning-to-action failures, which are a different and harder problem about last-mile reach and community trust.

---

## Category E: Limitations & Next Steps

**Q17: What are your biggest limitations?**
> Three honest ones: (1) CPDs are based on physics-informed priors, not fitted to a large historical dataset — we have maybe 5 confirmed multi-hazard cascade events in India with good documentation. (2) The impact layer uses OSM data which is incomplete in remote Himalayan areas. (3) Sensor data availability — real-time slope stability monitoring doesn't exist for most Indian catchments, so the rain-based proxy is necessary but imperfect.

**Q18: What would production deployment require?**
> Three things IMD/NDMA/GSI don't currently provide through APIs: (a) a near-real-time API for gridded rainfall at Himalayan catchment scale, (b) slope stability monitoring data from GSI for high-risk zones, (c) agreed alert escalation protocols between district SDMAs. The technical system is ready — the policy integration is the long path.

**Q19: Why did you scope to one hazard pair instead of trying to cover more?**
> Because scope honesty is part of the design. We can demonstrate one cascade chain with documented backtest data. Claiming to handle all hazard pairs without data to back it up would be worse than saying clearly: "This works for rainfall → GLOF → flood. The same architecture extends to cyclone → storm surge → coastal flood or cloudburst → debris flow → flash flood with region-specific calibration." A focused, validated claim beats a broad, unvalidated one.

---

## Demo Flow (4 minutes)

1. **Open `demo/CascadeIQ_Demo.html`** in browser (no internet needed after first load)
2. **Overview tab** (30s): "Here's the gap — one sentence. Here's the causal chain."
3. **Replay tab** (2m): Click Play. Pause at T-24h. Point to ORANGE, read the action. Jump to T=0. "12 hours of lead time. 6–9 hours for communities to act."
4. **Dashboard tab** (1m): "This is what the live dashboard would show. Map of hazard nodes. Full causal path. Impact breakdown. Authority verification queue."
5. **Methodology tab** (30s): "Physics defines structure. AI calibrates probabilities. Every alert shows its causal chain. Human verifies before it reaches the public."

---

*Last updated: September 2026 · Version 0.1.0 · Indradhanu PCCOE 2026*
