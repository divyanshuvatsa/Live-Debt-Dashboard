# 🔴 JCL Live Debt Dashboard

**A live, Excel-synced debt monitoring dashboard with built-in offline AI analyst.**

> **Live Excel Sync** · **No API Keys Required** · **Fully Offline AI** · **Deploy in 5 Minutes**

---

## 📺 What This Does

This dashboard reads `JCL_Debt_Model.xlsx` **directly** — when you update inputs in the Excel file (financials, rates, outstandings), all KPIs, covenants, and AI insights update automatically.

**Plus:** A built-in rule-based AI analyst answers ~30 question types about the portfolio (risk, covenants, leverage, prepayment strategy, etc.) — no Gemini, no Groq, no API keys, no internet required.

---

## 🚀 Quick Start

### **Option A: Run Locally** (recommended for live Excel editing)

```bash
# 1. Clone or download this repo
git clone https://github.com/divyanshuvatsa/Live-Debt-Dashboard.git
cd Live-Debt-Dashboard

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the dashboard
streamlit run live_main.py
```

Browser opens at http://localhost:8501

---

### **Option B: Deploy to Streamlit Cloud** (for sharing)

See **[Deployment Section](#-deploying-to-streamlit-cloud)** below.

---

## 📁 Folder Structure

```
Live-Debt-Dashboard/
│
├── .streamlit/
│   └── config.toml              ← Theme & server config
│
├── core/
│   ├── __init__.py
│   ├── financial_logic.py       ← Engine: WAC, DSCR, ICR, covenants
│   ├── board_memo.py            ← Auto-generates Word memo
│   └── ai_analyst.py            ← (Legacy — not used; replaced by rule_based)
│
├── ui/
│   ├── __init__.py
│   ├── dashboard.py             ← Main UI / tabs / charts
│   ├── theme.py                 ← Custom CSS styling
│   └── insights.py              ← Static insights logic
│
├── data/
│   ├── __init__.py
│   └── jcl_data.py              ← Fallback hardcoded data (used if Excel missing)
│
├── .gitignore
├── requirements.txt             ← Python dependencies
├── README.md                    ← This file
│
├── 🆕 live_main.py              ← ENTRY POINT — run this!
├── 🆕 live_jcl_data.py          ← Live Excel reader (cached, hash-based)
├── 🆕 rule_based_analyst.py     ← Offline AI (no API needed)
│
└── 📊 JCL_Debt_Model.xlsx       ← Source data (REQUIRED!)
```

---

## ⚙️ Setup Instructions (Step-by-Step)

### **STEP 1: Verify Python is Installed**

```bash
python --version
```

You should see `Python 3.9` or higher. If not, install from https://python.org

---

### **STEP 2: Clone or Download This Repo**

**If using git:**
```bash
cd Desktop
git clone https://github.com/divyanshuvatsa/Live-Debt-Dashboard.git
cd Live-Debt-Dashboard
```

**If downloading ZIP:**
1. Click "Code" → "Download ZIP" on GitHub
2. Extract to `Desktop/Live-Debt-Dashboard/`
3. Open Command Prompt:
   ```bash
   cd Desktop\Live-Debt-Dashboard
   ```

---

### **STEP 3: Install Dependencies**

```bash
pip install -r requirements.txt
```

This installs:
- `streamlit` — web framework
- `pandas` — data handling
- `openpyxl` — Excel reading
- `plotly` — charts
- `python-docx` — Word memo export
- `xlsxwriter` — Excel export

---

### **STEP 4: Run the Dashboard**

```bash
streamlit run live_main.py
```

Browser opens at http://localhost:8501

You should see:
- 🟢 Red banner: "LIVE · Live Debt Dashboard · Excel: [timestamp]"
- Sidebar showing Excel file path
- 6 tabs: Overview, Repayment, Covenants, Scenarios, AI Analyst, Export

---

## 🔄 Live Excel Sync Workflow

### **Edit Excel → See Updates in Dashboard:**

1. Open `JCL_Debt_Model.xlsx` in Excel
2. Edit any of these inputs:
   - **Instructions tab Section A** (As-of date, FX rate, Toggle)
   - **Instructions tab Section B** (8 benchmark rates)
   - **Instructions tab Section C** (All financials)
   - **Facility Master Col K** (Outstanding amounts)
   - **Facility Master Col Q** (Effective rates)
3. Save the Excel (Ctrl+S)
4. Go back to dashboard, click **🔄 Reload from Excel** in sidebar
5. All metrics, charts, and AI insights update with new values ✅

### **Test it:**

1. Note current EBITDA on Overview tab (should be ₹383.96 Cr)
2. Open Excel → Instructions tab → cell C25 → change to `500`
3. Save Excel
4. Click "Reload from Excel" in dashboard
5. Watch DSCR rise from 3.49x → ~4.6x

---

## 🤖 The Rule-Based AI Analyst

Located in `rule_based_analyst.py` — uses **deterministic financial rules** to answer questions. No LLM, no API, no internet.

### **What it can answer:**

**Portfolio Overview:**
- "What's our total annual interest cost?"
- "What's our weighted average cost?"
- "Show me a financial position summary"

**Risk Analysis:**
- "What's the biggest risk in this portfolio?"
- "Which covenant is closest to breach?"
- "Explain the SIB Current Ratio issue"
- "What's our refinancing risk?"

**Stress Testing:**
- "Which covenant breaks if EBITDA drops 15%?"
- "What's the impact of a 50 bps rate hike?"
- "Show me severe stress scenario"

**Action Items:**
- "Which term loan should we prepay first?"
- "What should we prioritise in the next lender review?"
- "Give me strategic recommendations"

**3 Auto-Generated Insights** appear on the AI tab — these update with the data.

---

## ☁️ Deploying to Streamlit Cloud

### **STEP 1: Push Repo to GitHub**

```bash
cd Live-Debt-Dashboard
git add .
git commit -m "Initial commit: Live Debt Dashboard"
git push origin main
```

### **STEP 2: Deploy on Streamlit Cloud**

1. Go to https://share.streamlit.io
2. Click **"New app"**
3. Configure:
   - **Repository:** `divyanshuvatsa/Live-Debt-Dashboard`
   - **Branch:** `main`
   - **Main file path:** `live_main.py` ⚠️ (NOT `main.py`)
4. Click **Deploy**
5. Wait 3–5 minutes for build

### **STEP 3: Verify Deployment**

Once live, you should see:
- 🟢 Red banner at top
- Sidebar with Excel file info
- All 6 tabs working
- AI tab answering questions immediately

### **NO Secrets Required!**

Unlike v1/v2, you do **NOT** need to set:
- ❌ GEMINI_API_KEY
- ❌ GROQ_API_KEY
- ❌ Any other secrets

---

## ⚠️ Important: Excel Updates on Cloud

**Locally:** Edit Excel → Save → Click Reload → Done ✅

**On Streamlit Cloud:** The Excel is read from GitHub. To update:

```bash
# Edit Excel locally, then:
git add JCL_Debt_Model.xlsx
git commit -m "Update Excel data"
git push origin main
```

Streamlit Cloud will auto-redeploy with the new Excel.

**TL;DR:** Use locally for true live editing. Use cloud for sharing/viewing.

---

## 🧪 Verify Everything Works

After deployment, check these:

✅ **Overview tab:** Shows ₹3,410.7 Cr total exposure, 34 facilities  
✅ **Repayment tab:** Shows 3 TLs (RBL, YBL, Bajaj) with quarterly schedule  
✅ **Covenants tab:** Shows 23 Compliant + 1 Near Breach (SIB Current Ratio)  
✅ **Scenarios tab:** Sliders work, recalculates DSCR/ICR live  
✅ **AI Analyst tab:** 3 insight cards visible, suggested questions clickable  
✅ **Export tab:** Can download board memo as Word doc  

---

## 🐛 Troubleshooting

| Issue | Fix |
|---|---|
| "Excel not found" banner | Ensure `JCL_Debt_Model.xlsx` is in repo root |
| Module not found error | Run `pip install -r requirements.txt` |
| Dashboard shows hardcoded data | Click "Reload from Excel" in sidebar |
| Streamlit Cloud build fails | Check `requirements.txt` versions |
| AI Analyst gives "general" response | Use keywords from suggested questions |
| Changes don't appear after Excel edit | Click "Reload from Excel" or refresh browser |

---

## 📊 Data Flow

```
JCL_Debt_Model.xlsx
        ↓
[live_jcl_data.py] reads with MD5 hash caching
        ↓
[FinancialLogic engine] computes WAC, DSCR, ICR, covenants
        ↓
[ui/dashboard.py] renders 6 tabs
        ↓
[rule_based_analyst.py] answers questions using rules
```

---

## 🔧 Configuration

### **Custom Excel Path**

By default, the dashboard looks for `JCL_Debt_Model.xlsx` in:
1. Same folder as `live_main.py`
2. `./data/JCL_Debt_Model.xlsx`
3. Current working directory

**To use a custom path:**

```bash
# Windows PowerShell
$env:JCL_EXCEL_PATH = "C:\path\to\JCL_Debt_Model.xlsx"
streamlit run live_main.py

# Linux/Mac
export JCL_EXCEL_PATH=/path/to/JCL_Debt_Model.xlsx
streamlit run live_main.py
```

---

## 📝 What's New vs Old Dashboard

| Feature | v1 (`main.py`) | v2 (Gemini/Groq) | **Live (`live_main.py`)** |
|---|---|---|---|
| Excel sync | ❌ Hardcoded | ❌ Hardcoded | ✅ **Live read** |
| AI Analyst | ❌ None | ⚠️ API required | ✅ **Offline rules** |
| API keys needed | None | Gemini/Groq | ✅ **None** |
| Internet required | Live FX/SOFR | Yes | ✅ **No** |
| Setup complexity | Easy | Medium | ✅ **Easiest** |
| Org policy issues | None | API blocks | ✅ **None** |

---

## 🎯 For Submissions / Demos

When demoing to Paras Sir or management:

1. **Live Sync demo:** Open Excel, change EBITDA, save, click reload → "watch the DSCR change in real-time"
2. **AI demo:** Click "What's the biggest risk?" suggested question → instant rule-based answer
3. **No API hassle:** "This works offline, no API keys needed, no IT approval required"

---

## 📞 Support

If you hit issues:

1. Check the troubleshooting table above
2. Verify `JCL_Debt_Model.xlsx` is in the repo root
3. Check that `live_main.py` is set as the main file in Streamlit Cloud
4. Verify Python version is 3.9+

---

## 📜 Credits

- **Data Model:** Jindal Coke Limited (JCL) Debt Model, 21-Apr-2026
- **Mentor:** Paras Sir
- **Author:** Divyanshu Vatsa
- **Framework:** Streamlit · Pandas · Plotly · openpyxl

---

**Built for live debt monitoring · No API · No Internet · Always works** 🚀
