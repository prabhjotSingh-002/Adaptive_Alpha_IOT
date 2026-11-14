# Cooja GUI Presentation & Demo Setup Guide
## AdaptiveAlpha IoT — Live Simulation & Teacher/Examiner Demo

Ye guide Cooja Network Simulator ko **live visual demonstration (PPT / Teacher / Project Review)** ke liye set up karne ka step-by-step manual hai.

---

## 1. Quick Launch Commands (Terminal Se)

### Option A: 9-Node Full Network (Root + 8 Sensors) — ⭐ Best for Presentation
```bash
cd /home/vanitas_archiviste/myDEV_linux/adaptiveAlpha_IOT

# X11 display permission (ek baar terminal mein do)
xhost +local:docker

# 9-node live visual simulation run karo
python3 host/run_experiment.py --phase 5 --mode B3 --clients 8 --seed 123456 --gui
```

### Option B: Quick 3-Node Demo (Root + 2 Sensors)
```bash
python3 host/run_experiment.py --phase 5 --mode B3 --clients 2 --seed 123456 --gui
```

---

## 2. Professional Window Layout Setup (Screen Arrangement)

Jab Cooja khule, apni screen ko is tarah arrange karo (4 windows):

```
+--------------------------------------------------------------------------+
|  Top Toolbar: [Start/Pause] [Step] [Reload] [Speed Limit: 1X / 2X]       |
+---------------------+---------------------------+------------------------+
|                     |                           |                        |
|   1. NETWORK MAP    |      2. MOTE OUTPUT       |   3. RADIO MESSAGES    |
|   (2D Nodes, IDs,   |  (Filtered Serial Logs:   |  (Wireshark-like 15.4  |
|    LEDs, Range)     |   e.g. Filter = "RX2")    |     Frame Sniffer)     |
|                     |                           |                        |
+---------------------+---------------------------+------------------------+
|                                                                          |
|                     4. TIMELINE (LOGIC ANALYZER)                         |
|      (Radio Duty Cycle: Blue = Transmit, Green = Receive, Grey = Sleep)  |
|                                                                          |
+--------------------------------------------------------------------------+
```

---

## 3. Charon Windows Ki Step-by-Step Settings

### Window 1: Network Map (Left Side)
1. **Zoom In:** Upar menu mein **`Zoom` -> `Zoom in`** par 2–3 baar click karo taaki nodes bade aur spacious dikhein.
2. **Visual Skins (View Menu):** **`View`** menu kholo aur ye 4 options **ON (Checked)** karo:
   - ✅ **`Node IDs`** — Nodes par bade numbers (1, 2, 3...) aayenge.
   - ✅ **`LEDs`** — Packet transmit/receive hone par nodes ke virtual Red/Green LEDs flash honge.
   - ✅ **`Radio traffic`** — Transmit hone par green directional rays aur transmission circles aayenge.
   - ✅ **`Wireless range`** — 50-meter radio coverage circle dikhega.

### Window 2: Timeline (Logic Analyzer — Bottom Side)
1. Agar Timeline khuli na ho: Top menu se **`Tools` -> `Timeline`** kholo.
2. Is window ko screen ke neeche **horizontal strip** ki tarah stretch kar do.
3. Har node (1, 2, 3...) ka dedicated track dikhega:
   - **Blue bar:** Node ne radio se packet transmit kiya (TX).
   - **Green bar:** Root ne packet hawa se receive kiya (RX).
   - **Cyan/Grey line:** Radio listen / low-power duty cycling.

### Window 3: Radio Messages (Packet Sniffer — Center Right)
1. Top menu se **`Tools` -> `Radio messages`** kholo.
2. Ye Wireshark ki tarah kaam karta hai:
   - Hawa mein travel karta hua har 802.15.4 packet yahan live capture hota hai.
   - Packet ka **Time, From Node, To Node, Length (Bytes)** dikhta hai.
   - 37-byte, 47-byte, 67-byte authenticated frames yahan visually verify hote hain.

### Window 4: Mote Output (Serial Logs — Center Top)
1. Cooja by default har 125ms par battery status print karta hai (`POLICY`), jo screen par tezi se scroll hota hai.
2. **Spam filter karne ke liye:** Window ke neeche **`Filter:`** box mein likho:
   - **`RX2`** 👉 **Best for Demo!** Sirf Root par authenticated & accepted readings dikhayega.
   - **`GEN`** 👉 Sensors kab-kab reading generate kar rahe hain sirf wo dikhayega.
   - **`SWITCH`** 👉 Jab adaptive policy cipher ya batch cap badalti hai sirf wo dikhayega.

---

## 4. Teacher / Examiner Ko Demo Kaise Present Karein (Speaking Script)

Presentation ke dauran simulation chala kar examiner ko ye 5 points point-out karke batao:

### Point 1: Topology Explain Karo (Network Window)
> *"Sir/Ma'am, screen ke left par humara 6LoWPAN IoT sensor network hai. Node 1 humara RPL Root (Base Station) hai, aur baaki Node 2 se Node 9 remote sensors hain jo temperature/sensing readings collect kar rahe hain."*

### Point 2: Start Dabao & Radio Traffic Dikhao (Timeline & Network)
> *(Toolbar mein **Start/Pause** dabao, Speed **1X** ya **2X** rakho)*  
> *"Jaise hi simulation start hui, aap Network map par green communication rings dekh sakte hain. Neeche Timeline analyzer mein dekhiye: jab Sensor packet bhejta hai toh Blue bar aati hai aur Root par real-time Green receive bar banti hai."*

### Point 3: Wire Format & Encryption (Radio Messages Window)
> *"Yahan Radio Messages table mein dekhiye: har packet ka size exactly 37 bytes hai (11-byte AAD header + 10-byte encrypted reading + 16-byte cryptographic MAC tag). Koi bhi data plain text mein air par travel nahi kar raha hai."*

### Point 4: Cryptographic Authentication (Mote Output Window)
> *(Filter mein `RX2` type karke dikhao)*  
> *"Root node par `RX2` logs dekhiye. Root har packet ka 16-byte MAC authentication tag decrypt aur verify karta hai. Agar koi packet inject ya replay kiya jaye, toh Root use reject karta hai. Yahan authenticated reading aur anti-replay counter zero-failure ke saath deliver ho rahe hain."*

### Point 5: Adaptive Policy (B3 / B6 / P1 Logic)
> *"Humara core research contribution adaptive policy hai: Node apni residual battery aur queue deadline ke hisaab se dynamically decide karta hai ki kab AES use karna hai aur kab low-power Ascon-128 cipher switch karna hai taaki network ki lifetime maximum extend ho sake."*

---

## 5. Important Shortcuts & Controls

| Action | Kaise Karein |
|---|---|
| **Simulation Start / Pause** | Toolbar par **`Start/Pause`** button |
| **Fast Forward** | Toolbar par `Speed limit:` ko **`2X`** ya **`20X`** select karo |
| **Step-by-Step Packet** | **`Step`** button dabao (microsecond precision) |
| **Clean Exit** | Cooja ki main window ko **Cross (X)** karke band kar do |
| **Zoom Reset** | Network window mein `Zoom -> Zoom in / Zoom out` |
