# PHA Landz Dispatcher Project

This project automates **Pixel Heroes Adventure (PHA) LandZ dispatches** by selecting the optimal combination of heroz to maximize buffs and prioritize high-grade missions.

---

## 📋 Overview
- **Language:** Python 3.9+
- **Purpose:** Automate dispatching heroz to LandZ buildings in PHA.
- **Features:**
  - Automatically selects heroz to maximize buffs and total points.
  - Respects key heroz requirement (grade ≥ building grade).
  - Displays detailed plan in dry-run mode.
  - Can execute dispatches automatically with retries.
  - Optionally claims rewards before planning.

---

## ⚠️ Important Notice
I built this script for **my own assets** and tailored it to my needs:

- I **do not own any Genesis Heroz**, so Genesis support is not yet implemented.
- Mercenary hiring is **not yet implemented**.
- Mythical dispatch logic is implemented but **not tested** (I don’t own Mythical Heroz).
- I will **never ask you for your Bearer token** or DM you first.
- **Nothing here is investment advice** — it’s just an automation tool for convenience.
- I am **not part of the PHA development team**, I am just a player.
- This code should be run **locally** — never share your Bearer token with anyone.
- I am not responsible for any potential data or asset loss. **Stay safe!**
- I only use Linux, so I have **not tested this on Windows or Mac** — please test and let me know if instructions need adjustments.

**Contact:**
- Discord: `life_tester`
- Email: `lifetester.dev@gmail.com`

**Tips/Thanks:**
- Ronin wallet: `0xD4Ec419216ABd8286005a4797fd1C183Bd9E6649`
- Ethereum wallet: `0xB6CF6aF6C4D200835ffa7088a7Eef40110C7c953`

I gladly accept kind words, NFTs, $RON, $ETH, coffee, or any other support ❤️

---

## 🛠️ Future Plans
If PHA continues supporting LandZ dispatch, I plan to:

- Improve hero selection logic for buff completion.
- Implement mercenary hiring (Primal and Genesis).
- Add full support for Genesis Heroz.

---

## ⚙️ Requirements
- Python 3.9 or newer
- Add Python to PATH during installation (important for Windows users)
- Install dependencies:
```bash
pip install -r requirements.txt
```

---

## 📸 Step-by-Step: Getting Your Bearer Token
1. Open [Pixel Heroes Adventure DApp](https://dapp.pixelheroes.io/) in Chrome or Firefox.
2. Log in.
3. Open **Developer Tools** (F12 or right-click → Inspect).
4. Go to **Network** tab.
5. Refresh the page.
6. Click on any request.
7. Go to the **Headers** tab.
8. Find the **Authorization** header, copy the value after `Bearer`.

### Example Bearer Token:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtZWdhdXNlciIsImlhdCI6MTY4ODc0MDAwMCwiZXhwIjoxNjg4NzQ2MDAwfQ.signatureexample
```

**Screenshot Example:**
![Bearer Token Example](docs/images/bearer-token-example.png)

---

## 📥 Installation and Setup

### Clone Repository
```bash
git clone https://github.com/your-username/pha-landz-dispatch.git
cd pha-landz-dispatch
```

### Install Dependencies
#### Linux / macOS
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Windows (PowerShell)
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Check if you have python installed:
```bash
python --version
```
If not found, install from [python.org](https://www.python.org/downloads/).

---

## 🖥️ Platform Commands
Linux/macOS:
```bash
python3 main.py --token <TOKEN>
```
Windows (PowerShell):
```powershell
py main.py --token <TOKEN>
```
Ensure Python is in PATH.

---

## 📜 CLI Arguments
| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--token` | ✅ | — | Bearer token from browser network tab |
| `--region` | ❌ | 1 | 1 = Meta Toy City, 2 = Ludo City |
| `--confirm` | ❌ | False | Actually perform dispatches |
| `--all` | ❌ | False | Dispatch all missions instead of one |
| `--max-dispatches` | ❌ | 999999 | Safety limit for number of dispatches |
| `--claim-first` | ❌ | False | Claims rewards before planning |

---

## ▶️ Full Example Command
```bash
python main.py --token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... --region 2 --claim-first --confirm --all
```

This will:
- Use region **2** (Ludo City) to claim the play points
- Claim rewards before planning
- Confirm dispatches
- Dispatch **all available missions**

I recommend you don't use --confirm first, just pass the token and see the simulation results. After that, use --confirm to dispatch just the first one.

---

## 🔍 Example Output
```
=== Dispatch Plan ===
01. - #3540 | Tavern | Grade=Epic | Base=250 | Buffs=1 x 30% [Epic+ Base Primal HeroZ x2 [...]] |
     Est.Total=325.0 | Chosen=[...] | Reserved=[—] | Dispatch guaranteed with key hero (≥ Epic);
     completed 1 buff(s).
    Requirements:
      - Epic+ Base Primal HeroZ x2: createType=2 grade=2(1) race=-1 star=-1 need=2
```

---

## 🧑‍💻 Contributing
Feel free to open issues, send PRs, or suggest improvements. Contact me via Discord (`life_tester`) or email (`lifetester.dev@gmail.com`).

---

## 📄 License
MIT License — free to use, modify, and share.
