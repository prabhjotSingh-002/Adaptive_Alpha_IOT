# Windows Setup & Running Guide
## AdaptiveAlpha IoT — Safe & Efficient Execution Guide for Windows Users

Ye guide un teammates ke liye hai jo **Windows (Windows 10 / Windows 11)** use karte hain aur is IoT project ko bina kisi crash, line-ending error (`^M`), ya path failure ke chalana chahte hain.

---

## 1. The Golden Rule (Sabse Badi Savdhani) ⚠️

> **DO NOT** run this project directly inside Windows Command Prompt (CMD) or native Windows PowerShell!  
> **Kyun?** Kyunki project ke andar Linux bash scripts, Contiki-NG build toolchains, aur Docker bind mounts hain jo Windows native path separators (`\`) aur CRLF line-endings par crash ho jaate hain.

👉 **Sahi aur 100% Reliable Tarika:** **WSL2 (Windows Subsystem for Linux) + Docker Desktop**.  
Isse Windows ke andar ek complete, real Ubuntu Linux environment milta hai.

---

## 2. Step-by-Step Setup Instructions

### Step 1: WSL2 (Ubuntu) Install Karo (Sirf 2 Minute)
1. Apne Windows computer par Start menu mein **PowerShell** search karo.
2. Uspar Right-Click karke **"Run as Administrator"** select karo.
3. Ye single command chalao:
   ```powershell
   wsl --install
   ```
4. Computer restart karne ko bolega, **Restart** karo.
5. Restart hone ke baad ek black Ubuntu terminal khulega. Apna manpasand **Username** aur **Password** daal do.
*(Windows 11 users ke liye: Windows 11 mein **WSLg** automatically hota hai, jisse Cooja ki GUI window seedha Windows app ki tarah pop-up ho jaati hai bina kisi extra configuration ke!)*

---

### Step 2: Docker Desktop for Windows Setup
1. Official website se [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) download aur install karo.
2. Install karne ke baad **Docker Desktop** open karo aur upar **Settings (Gear Icon)** par jao:
   - **General Tab:** Ensure karo ki ✅ **"Use the WSL 2 based engine"** par tick ho.
   - **Resources -> WSL Integration:** Wahan **"Ubuntu"** ke aage toggle switch ko **ON** kar do.
3. **Apply & Restart** par click karo.

---

### Step 3: Git CRLF & Folder Location (CRITICAL STEP) ⚠️
Windows Git by default Linux files ke line-endings (`\n`) ko Windows format (`\r\n`) mein badal deta hai, jisse bash scripts `^M: command not found` error dekar fail ho jaati hain.

Apna **Ubuntu Terminal** kholo aur ye commands chalao:

```bash
# 1. Windows CRLF auto-conversion ko permanently band karo:
git config --global core.autocrlf false

# 2. Project ko C: drive mein MAT rakhna! Seedha Ubuntu ke home directory mein clone/copy karo:
cd ~

# 3. Yahan project folder mein jao:
# git clone <repository-url>
cd adaptiveAlpha_IOT
```

*(Tip: Agar aapko Windows File Explorer se Ubuntu ki files dekhni ya edit karni hain, toh Windows Explorer ke address bar mein type karo: `\\wsl$\Ubuntu\home\<your-username>\adaptiveAlpha_IOT` — aap VS Code ya Notepad se files aaram se access kar sakte ho).*

---

### Step 4: Verification (Docker Check)
Ubuntu terminal ke andar ye check karo ki Docker chal raha hai ya nahi:
```bash
docker ps
```
Agar koi error nahi aaya aur container list aayi, matlab setup 100% ready hai!

---

## 3. Running the Project on Windows

Ab aapka terminal 100% Linux environment ban chuka hai. Aap exact wahi commands chala sakte hain jo guide mein hain:

### A. Results Dashboard Chalana (Web GUI)
```bash
cd ~/adaptiveAlpha_IOT
python3 host/run_dashboard.py
```
- Command chalane ke baad terminal bolega `Starting on http://0.0.0.0:5000`.
- Apne Windows ke **Chrome ya Edge Browser** mein kholo:
  👉 **`http://localhost:5000`**
- Windows automatic port forward karta hai, saare charts aur comparison tables browser mein dikh jayenge!

---

### B. Cooja GUI Simulation Chalana (Live Visual Nodes & Radio Traffic)

#### Windows 11 Users (Direct & Automatic via WSLg):
Windows 11 par koi X11 server install nahi karna padta. Seedha ye command chalao:
```bash
cd ~/adaptiveAlpha_IOT
xhost +local:docker
python3 host/run_experiment.py --phase 5 --mode B3 --clients 8 --seed 123456 --gui
```
- Cooja ki window ek **native Windows software** ki tarah aapke taskbar par open ho jayegi!

#### Windows 10 Users (Agar WSLg na ho):
Agar aap Windows 10 par ho aur GUI window na khule:
1. Free software **[VcXsrv Windows X Server](https://sourceforge.net/projects/vcxsrv/)** install karo.
2. VcXsrv (XLaunch) open karo, **"Disable access control"** par tick karo aur Finish karo.
3. Ubuntu terminal mein ye set karo:
   ```bash
   export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
   ```
4. Fir wahi experiment command chalao.

---

### C. Headless Experiments (Fast Data Collection Mode)
Agar visual GUI nahi dekhna aur sirf results / data generate karna hai:
```bash
# 8 Clients, Z1 Hardware Target, Power Model
python3 host/run_experiment.py --phase 5 --mode B3 --clients 8 --seed 123456 --power-model --target z1
```
Run complete hone par terminal mein `passed` aayega aur dashboard par refresh karne par naya data add ho jayega.

---

## 4. Troubleshooting & Quick Fixes

| Issue / Error | Wajah (Cause) | Solution |
|---|---|---|
| `/bin/bash^M: bad interpreter` | File Windows format (CRLF) mein save ho gayi | Run: `git config --global core.autocrlf false` aur repo dobara clone karo ya `dos2unix` chalao. |
| `Cannot connect to the Docker daemon` | Docker Desktop mein WSL integration off hai | Docker Settings -> Resources -> WSL Integration -> Ubuntu toggle **ON** karo aur Docker restart karo. |
| `OutOfMemory` ya WSL Slow ho raha hai | Windows ne WSL ko limited RAM di hai | Windows User folder (`C:\Users\<Name>\`) mein `.wslconfig` file banao aur likho:<br>`[wsl2]`<br>`memory=4GB` |
| Cooja window grey dikh rahi hai | Java X11 repaint delay | Window ke top-right corner se **Maximize `^`** button dabao ya border resize karo. |
