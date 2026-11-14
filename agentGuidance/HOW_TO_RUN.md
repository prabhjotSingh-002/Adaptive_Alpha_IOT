# Project Chalane ka Guide
## AdaptiveAlpha IoT — Teacher/Teammate ko Dikhane ke liye

**Prerequisites:** Docker chalu ho, project directory mein ho.

---

## 1. Dashboard — Sabse Pehle Yahi Chalao

Dashboard se poore project ke results ek jagah dikhte hain.

```bash
cd /home/vanitas_archiviste/myDEV_linux/adaptiveAlpha_IOT
python3 host/run_dashboard.py
```

Browser mein kholo: **http://localhost:5000**

Dashboard mein dikhai dega:
- Phase 2 se Phase 5 tak ke saare 171 runs
- Har mode (B1/B2/B3/B4/B5/B6/P1) ki energy, PDR, latency
- Bootstrap confidence interval ke saath charts
- Kisi bhi run pe click karo — detail dekhna

**Band karna ho to:** Terminal mein `Ctrl+C`

---

## 2. Naya Experiment Chalana (Headless — Normal Mode)

Yeh normal experiment run hai — results automatically save hote hain.

### Quick test (2 clients, ~2 min):
```bash
python3 host/run_experiment.py --phase 5 --mode B3 --clients 2 --seed 123456
```

### Full pilot run (8 clients, Z1 target, energy model, ~3 min):
```bash
python3 host/run_experiment.py --phase 5 --mode B3 --clients 8 --seed 123456 --target z1 --power-model
```

### Teeno policy modes ek ke baad ek:
```bash
python3 host/run_experiment.py --phase 5 --mode B3 --clients 8 --seed 123456 --target z1 --power-model
python3 host/run_experiment.py --phase 5 --mode B6 --clients 8 --seed 123456 --target z1 --power-model
python3 host/run_experiment.py --phase 5 --mode P1 --clients 8 --seed 123456 --target z1 --power-model
```

Run khatam hone ke baad: Dashboard pe `↻ Refresh` dabao — nayi run table mein dikhegi.

---

## 3. Cooja GUI — Live Simulation Dekhna

Jab experiment chal raha hota hai tab nodes visually dikhte hain.

```bash
python3 host/run_experiment.py --phase 5 --mode B3 --clients 2 --seed 123456 --gui
```

**Kya dikhega:**
- Cooja window khulegi (~30 sec build ke baad)
- 3 nodes map pe (1 root + 2 sensors)
- Nodes ke beech radio packets fly karte dikhenge
- Neeche har node ka serial log live aata hai

**Dhyan rakho:** GUI mode mein results save nahi hote — sirf visual dekh sakte ho. Research results ke liye `--gui` flag mat lagao.

**Window band karo** jab dekh lo — experiment automatically stop ho jayega.

---

## 4. Statistics Generate Karna

```bash
python3 host/run_analysis.py --phase 4 --phase 5 --output results/analysis.json
```

Terminal mein print hoga:
- Har mode ki mean energy, PDR, p95 delay
- 95% bootstrap confidence intervals
- Phase 4 baseline (B1) se comparison (% change)
- Policy runs ka summary

---

## 5. Plots Generate Karna (PNG files)

```bash
# Phase 4 static baselines (B1/B2/B4/B5)
python3 host/run_plots.py --phase 4 --output results/phase_04/figures/phase4.png

# Phase 5 policy arms (B3/B6/P1) — specific runs
python3 host/run_plots.py \
  --runs results/phase_05/20261114T120117290160Z-B3-8 \
         results/phase_05/20261114T121756262964Z-B6-8 \
         results/phase_05/20261114T122031479887Z-P1-8 \
  --output results/phase_05/figures/phase5-policy.png
```

PNG file ban jayegi — open karo ya dashboard pe dikhega.

---

## 6. Unit Tests Chalana

```bash
# Policy tests (17 tests)
python3 tests/unit/test_policy.py -v

# Metrics tests (18 tests)
python3 tests/unit/test_metrics.py -v

# Lifetime tests (3 tests)
python3 tests/unit/test_lifetime.py -v
```

Yeh Docker ke bina bhi chalte hain — pure Python.

---

## 7. Teacher/Teammate ko Demo Script

**Step 1 — Dashboard dikho (2 min)**
```bash
python3 host/run_dashboard.py
# Browser mein: http://localhost:5000
# Dikho: Phase Overview, Mode Comparison table, Charts
```

**Step 2 — Live experiment chalao (3 min)**
```bash
# Naya terminal kholo
python3 host/run_experiment.py --phase 5 --mode P1 --clients 2 --seed 999999
# Dikhao: Docker container start hota hai, firmware compile hota hai, simulation chalti hai
# Khatam hone ke baad dashboard pe refresh karo — nayi run dikhegi
```

**Step 3 — Cooja GUI dikho (2 min)**
```bash
python3 host/run_experiment.py --phase 5 --mode B3 --clients 2 --seed 123456 --gui
# Cooja window khulegi — nodes map pe, radio packets
# "Ye actual IoT simulation hai" — explain karo
```

**Step 4 — Statistics explain karo (2 min)**
```bash
python3 host/run_analysis.py --phase 4 --phase 5
# Terminal mein table print hoga
# B3/B6/P1 vs B1 comparison dikhao
# "Yahan dekho B4/B5 mein energy kam hai lekin latency 20x zyada hai"
```

**Step 5 — Code dikhao (optional, 5 min)**
```bash
# Policy logic
cat firmware/policy/policy.c | head -80

# Ek actual run ka result
cat results/phase_05/20261114T120117290160Z-B3-8/summary.json | python3 -m json.tool
```

---

## 8. Important Files — Jaldi Reference

| Kya | Kahan |
|---|---|
| Experiment chalana | `python3 host/run_experiment.py` |
| Dashboard | `python3 host/run_dashboard.py` |
| Statistics | `python3 host/run_analysis.py` |
| Plots | `python3 host/run_plots.py` |
| Phase 5 results | `results/phase_05/` |
| Phase 4 results | `results/phase_04/` |
| Phase 4 charts | `results/phase_04/figures/` |
| Policy firmware | `firmware/policy/policy.c` |
| Project status | `AFTER_PHASE5_STATUS.md` |
| Phase 6 context | `PHASE6_CONTEXT.md` |

---

## 9. Common Errors

**"permission denied while trying to connect to the Docker API"**
```bash
# sg docker se chalao
sg docker -c "python3 host/run_experiment.py --phase 5 --mode B3 --clients 2 --seed 123456"
```
Ya ek baar logout/login karo taaki docker group apply ho.

**"Cooja GUI nahi khul raha"**
```bash
xhost +local:docker   # X11 permission do Docker ko
python3 host/run_experiment.py --phase 5 --mode B3 --clients 2 --seed 123456 --gui
```

**"Dashboard pe charts nahi dikh rahe"**
- matplotlib Docker mein hai, host pe nahi — isliye `run_dashboard.py` Docker ke andar chalata hai
- Agar phir bhi nahi dikha: `curl http://localhost:5000/api/chart/energy` check karo

**Dashboard already chal raha hai — port busy**
```bash
python3 host/run_dashboard.py --port 8080
# Browser mein: http://localhost:8080
```
