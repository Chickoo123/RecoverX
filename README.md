<div align="center">

# 🔁 RecoverX

### AI-Powered Revenue Recovery Agent

**Built for the Razorpay AI Buildathon — AI Revenue Recovery Track**

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Groq](https://img.shields.io/badge/AI-Groq%20LLM-orange)](https://groq.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

*An autonomous agent that detects at-risk revenue, reasons about customer intent, and executes bounded recovery workflows — with a full audit trail.*

</div>

---

## 📑 Table of Contents

- [The Problem](#-the-problem)
- [The Solution](#-the-solution-neuro-symbolic-ai)
- [Key Features](#-key-features)
- [Results](#-simulation-results--metrics)
- [Architecture](#-architecture)
- [Tech Stack](#️-tech-stack)
- [Setup](#️-setup--local-installation)
- [Security](#-security-considerations)

---

## 🎯 The Problem

Standard payment recovery systems fall into two failure modes:

| Approach | Failure Mode |
|---|---|
| **Blind automated retries** | Increases gateway costs, retries on stolen/disputed cards (compliance risk) |
| **Fully manual intervention** | Doesn't scale, slow response to time-sensitive recovery windows |

When a transaction fails, customers often reply with context — *"My card was stolen"*, *"I'll pay next week"*, *"This charge is wrong"*. Traditional recovery systems **ignore this signal entirely**, treating every failure identically.

## 💡 The Solution: Neuro-Symbolic AI

RecoverX separates **perception** from **action** — a pattern used in real enterprise financial systems to keep LLMs out of the money-movement loop.

┌─────────────────────┐ ┌──────────────────────────┐
│ AI Perception │ intent │ Deterministic Rule │
│ Groq LLM │ ───────▶ │ Engine (Python) │
│ Reads unstructured │ │ 9 priority-ordered │
│ customer replies │ │ financial guardrails │
└─────────────────────┘ └──────────────────────────┘
│
▼
STOP · ESCALATE · RETRY · FOLLOW-UP


The LLM **never** triggers a financial action directly — it only classifies intent (`DISPUTE`, `FRAUD`, `PROMISE_TO_PAY`, `NONE`). All actual decisions flow through strict, auditable, deterministic rules.

---

## 🚀 Key Features

- **🔀 AI vs. Rules Comparison Toggle** — live dashboard toggle proving quantifiable ROI (**+21% recovery** with AI-augmented reasoning vs. static rules alone)
- **🛡️ Bounded Workflows & Guardrails** — hard stops on disputes and fraud, max-retry limits to prevent customer fatigue
- **📊 Real-Time Executive Dashboard** — dark-themed, animated, built for a live demo
- **🧾 Immutable Audit Trail** — every decision + the AI's natural-language reasoning is logged for compliance
- **⬇️ One-Click CSV Export** — full audit trail exportable for offline review

---

## 📊 Simulation Results & Metrics

Evaluated on a synthetic batch of **53 high-risk transactions**:

| Metric | Value |
|---|---:|
| Total Revenue at Risk | ₹6,52,305 |
| Recovered — *without* AI | ₹99,780 |
| Recovered — *with* AI | **₹1,20,734** (18.5%) |
| Attempt Success Rate | 40.5% |
| Safely Escalated (fraud / high-value) | ₹2,63,178 |
| Stopped by Guardrails (disputes / max retries) | ₹91,253 |

> **AI-augmented recovery outperformed rule-only recovery by +21%** on identical data — the toggle in the dashboard demonstrates this live.

---

## 🏗️ Architecture

Payment Gateway / CRM
│
▼
┌───────────────────┐
│ 1. DETECT │ Failed payment, checkout abandonment, overdue invoice
└───────────────────┘
│
▼
┌───────────────────┐
│ 2. DIAGNOSE (AI) │ Groq LLM reads customer_reply → intent + reasoning
└───────────────────┘
│
▼
┌───────────────────┐
│ 3. DECIDE (Rules) │ 9 priority rules: dispute→STOP, fraud→ESCALATE,
│ │ high-value→ESCALATE, promise→FOLLOW-UP, etc.
└───────────────────┘
│
▼
┌───────────────────┐
│ 4. EXECUTE │ RETRY · SEND_PAYMENT_LINK · SEND_REMINDER ·
│ │ ESCALATE · STOP · SCHEDULE_FOLLOW_UP
└───────────────────┘
│
▼
┌───────────────────┐
│ 5. VERIFY & MEASURE│ Simulated outcome verification, recovery totals
└───────────────────┘
│
▼
┌───────────────────┐
│ 6. AUDIT │ audit_log.json — full reasoning trail per transaction
└───────────────────┘



---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Flask |
| AI Engine | Groq API (`openai/gpt-oss-20b`) |
| Frontend | HTML5, Chart.js, Vanilla JS |
| Data | CSV (transactions), JSON (audit log) |

---

## ⚙️ Setup & Local Installation

```bash
# 1. Clone the repository
git clone https://github.com/Chickoo123/RecoverX.git
cd RecoverX

# 2. Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install flask groq python-dotenv

# 4. Configure environment variables
# Create a .env file in the root directory:
echo GROQ_API_KEY=your_api_key_here > .env

# 5. Run the application
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

---

## 🔒 Security Considerations

- **API Key Isolation** — Groq API key lives only in `.env`, excluded from version control via `.gitignore`
- **No Direct AI Execution** — the LLM only outputs intent tags; it has zero access to trigger payment actions, ensuring rule-based safety over all money movement
- **Development Mode Note** — Flask runs with `debug=True` for this hackathon demo; a production deployment would use a WSGI server (e.g. Gunicorn) with debug disabled

---

<div align="center">

**Built by Harshil Jitendra Desai** 

</div>