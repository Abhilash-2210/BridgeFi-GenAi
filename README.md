# BridgeFi

> **Closing the Loop Between Applicant Effort & Recruiter Response**

A dual-sided intelligence platform for skill-gap bridging, ghosting prevention & personal career analytics.

**"Not another resume parser. Not another tracker. Two sides. One solution."**

---

## 🚀 Quick Start (No npm, No React, No errors!)

### Prerequisites
- Python 3.9+
- pip

### 1. Clone & Setup

```bash
git clone https://github.com/your-username/bridgefi.git
cd bridgefi
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment (Optional)

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY for AI features
# The app works perfectly without an API key using smart mock data
```

### 4. Run the App

```bash
python app.py
```

Open **http://localhost:5000** in your browser. That's it! 🎉

---

## 🌐 Deployment

### Deploy to Render (Free)

1. Push to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your repo
4. Set environment variables:
   - `ANTHROPIC_API_KEY` = your key
   - `SECRET_KEY` = random string
5. Deploy!

### Deploy to Railway

```bash
railway login
railway init
railway up
```

---

## ✨ Features

### For Applicants
| Feature | Description |
|---------|-------------|
| **Application Tracker** | Full CRUD — track company, role, status, notes |
| **Ghosting Prediction Engine** | ML-style score using company, department, timing |
| **Skill-Gap Artifact Generator** | AI extracts missing skills + generates mini-project |
| **Hidden JD Signals** | Uncovers 10+ unstated job requirements |
| **Follow-up Generator** | AI drafts professional follow-up emails in 1 click |
| **Personal Dashboard** | Stats, charts, KPIs — all in one view |

### For Recruiters
| Feature | Description |
|---------|-------------|
| **Candidate Pipeline** | Full CRUD candidate management |
| **Skill Score + Honesty Score** | Rate candidates on skill level & learning agility |
| **One-Click Bulk Follow-up** | Update all pending candidates in 10 seconds |
| **Ghosting Risk Dashboard** | Your team's ghosting rate vs industry benchmark |
| **Radar Analytics** | Response rate, brand score, transparency metrics |

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3 + Flask |
| Database | SQLite (via SQLAlchemy) |
| Frontend | HTML5 + CSS3 + Vanilla JS |
| Charts | Chart.js |
| AI/LLM | Anthropic Claude API |
| Icons | Font Awesome 6 |
| Fonts | Google Inter |
| Deploy | Render / Railway / Heroku |

---

## 📁 Project Structure

```
bridgefi/
├── app.py                  # Main Flask application + all routes + DB models
├── requirements.txt        # Python dependencies
├── Procfile               # For Render/Heroku deployment
├── .env.example           # Environment variables template
├── README.md
├── templates/
│   ├── base.html          # Base layout with navbar
│   ├── index.html         # Landing page
│   ├── applicant.html     # Applicant dashboard
│   ├── recruiter.html     # Recruiter dashboard
│   └── analyzer.html      # Skill-gap AI analyzer
└── static/
    ├── css/style.css      # Full custom CSS (light theme)
    └── js/main.js         # Shared JS utilities
```

---

## 🧠 AI Features

The Skill-Gap Analyzer uses **Claude claude-sonnet-4-20250514** to:
- Extract all required skills from a JD
- Prioritize them (Critical / High / Medium / Low)
- Uncover 5+ hidden signals not written in the JD
- Generate a concrete runnable mini-project to bridge gaps
- Calculate a match score

**Without an API key:** The app uses intelligent mock analysis that still demonstrates all features.

---

## 📊 Ghosting Prediction Algorithm

Factors used:
- **Department base rate** (Engineering 30%, HR 55%, etc.)
- **Days since applied** (sigmoid function peaking at ~14 days)
- **Company type** (FAANG companies respond 25% more)
- **Best day to apply**: Tuesday = ~2× response rate

---

## 👥 Team

- **Rishi Raj** (24BCE10149)
- **Arnab Kumar** (24BCE11017)
- **Swastik Sinha** (24BEY10075)
- **Abhilash Singh** (24BCE10706)

**Track**: CSE / AI / Automation · VIT Bhopal

---

## 📄 License

MIT License — built for G-Ai Hackathon 2025
