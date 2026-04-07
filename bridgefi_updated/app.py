"""
BridgeFi - Closing the Loop Between Applicant Effort & Recruiter Response
A dual-sided intelligence platform for skill-gap bridging, ghosting prevention
& personal career analytics.
"""

import os
import json
import math
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# App Configuration
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "bridgefi-secret-key-2024")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///bridgefi.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
CORS(app)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ---------------------------------------------------------------------------
# Database Models
# ---------------------------------------------------------------------------
class Application(db.Model):
    """Tracks a job application submitted by an applicant."""
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), default="Engineering")
    status = db.Column(db.String(50), default="Applied")  # Applied | Interview | Offer | Ghosted | Rejected
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text, default="")
    job_url = db.Column(db.String(500), default="")
    ghosting_risk = db.Column(db.Float, default=0.0)   # 0.0 – 1.0
    follow_up_sent = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "company": self.company,
            "role": self.role,
            "department": self.department,
            "status": self.status,
            "applied_date": self.applied_date.strftime("%Y-%m-%d"),
            "last_updated": self.last_updated.strftime("%Y-%m-%d") if self.last_updated else "",
            "notes": self.notes,
            "job_url": self.job_url,
            "ghosting_risk": round(self.ghosting_risk * 100),
            "follow_up_sent": self.follow_up_sent,
        }


class Candidate(db.Model):
    """Tracks a candidate from the recruiter's perspective."""
    __tablename__ = "candidates"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), default="")
    status = db.Column(db.String(50), default="Under Review")  # Under Review | Shortlisted | Interview | Hired | Rejected
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)
    skill_score = db.Column(db.Float, default=0.0)   # 0.0 – 1.0
    honesty_score = db.Column(db.Float, default=0.0) # 0.0 – 1.0  (skill-gap honesty)
    notes = db.Column(db.Text, default="")
    response_sent = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "status": self.status,
            "applied_date": self.applied_date.strftime("%Y-%m-%d"),
            "skill_score": round(self.skill_score * 100),
            "honesty_score": round(self.honesty_score * 100),
            "notes": self.notes,
            "response_sent": self.response_sent,
        }


class SkillGapResult(db.Model):
    """Stores skill-gap analysis results."""
    __tablename__ = "skill_gap_results"

    id = db.Column(db.Integer, primary_key=True)
    jd_text = db.Column(db.Text, nullable=False)
    user_skills = db.Column(db.Text, default="")
    result_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Database Seeding
# ---------------------------------------------------------------------------
def seed_database():
    """Insert demo data so the app looks great on first run."""
    if Application.query.count() == 0:
        demo_apps = [
            Application(company="Google", role="Software Engineer L4", department="Search",
                        status="Interview", applied_date=datetime.now() - timedelta(days=12),
                        ghosting_risk=0.22, notes="Completed phone screen. Waiting for on-site invite."),
            Application(company="Microsoft", role="ML Engineer II", department="Azure AI",
                        status="Applied", applied_date=datetime.now() - timedelta(days=9),
                        ghosting_risk=0.47, notes="Strong match on JD. Applied via LinkedIn."),
            Application(company="Startup XYZ", role="Backend Developer", department="Product",
                        status="Ghosted", applied_date=datetime.now() - timedelta(days=28),
                        ghosting_risk=0.88, notes="No response after 4 weeks. Auto follow-up sent."),
            Application(company="Amazon", role="SDE-2", department="AWS",
                        status="Offer", applied_date=datetime.now() - timedelta(days=35),
                        ghosting_risk=0.08, notes="Received offer letter. Negotiating package."),
            Application(company="Flipkart", role="Data Scientist", department="Ads",
                        status="Rejected", applied_date=datetime.now() - timedelta(days=20),
                        ghosting_risk=0.15, notes="Got feedback: need more ML system design experience."),
            Application(company="Razorpay", role="Backend Eng", department="Payments",
                        status="Applied", applied_date=datetime.now() - timedelta(days=5),
                        ghosting_risk=0.31, notes="Applied through referral."),
        ]
        db.session.add_all(demo_apps)

    if Candidate.query.count() == 0:
        demo_candidates = [
            Candidate(name="Alice Johnson", email="alice@example.com", role="Frontend Developer",
                      status="Shortlisted", skill_score=0.87, honesty_score=0.91,
                      notes="Strong portfolio. Submitted skill-gap artifact for React performance."),
            Candidate(name="Bob Smith", email="bob@example.com", role="Data Scientist",
                      status="Under Review", skill_score=0.73, honesty_score=0.80,
                      notes="Missing PySpark experience. Learned it 2 weeks ago — high agility."),
            Candidate(name="Carol Davis", email="carol@example.com", role="DevOps Engineer",
                      status="Interview", skill_score=0.92, honesty_score=0.88,
                      notes="Excellent artifact — Kubernetes deployment pipeline. Scheduling final round."),
            Candidate(name="David Lee", email="david@example.com", role="Backend Developer",
                      status="Under Review", skill_score=0.65, honesty_score=0.70,
                      notes="Good fundamentals. Skill gap in distributed systems."),
            Candidate(name="Eva Patel", email="eva@example.com", role="ML Engineer",
                      status="Hired", skill_score=0.95, honesty_score=0.97,
                      notes="Exceptional candidate. Offer accepted."),
        ]
        db.session.add_all(demo_candidates)

    db.session.commit()


# ---------------------------------------------------------------------------
# Ghosting Risk Calculator (deterministic ML-style scoring)
# ---------------------------------------------------------------------------
DEPARTMENT_RISK = {
    "engineering": 0.30, "product": 0.40, "design": 0.35,
    "marketing": 0.50, "sales": 0.45, "hr": 0.55, "finance": 0.38,
    "data": 0.32, "ai": 0.28, "aws": 0.25, "cloud": 0.27, "search": 0.22,
}

def calculate_ghosting_risk(company: str, role: str, department: str, days_since_apply: int) -> dict:
    """
    Score ghosting probability using multiple signals.
    Returns a dict with risk score (0-100) and breakdown.
    """
    dept_key = department.lower().strip()
    base_risk = DEPARTMENT_RISK.get(dept_key, 0.40)

    # Days since apply sigmoid
    day_factor = 1 / (1 + math.exp(-0.15 * (days_since_apply - 14)))

    # Company size heuristic (FAANG-like companies respond faster)
    faang = ["google", "amazon", "microsoft", "apple", "meta", "netflix",
             "flipkart", "razorpay", "swiggy", "zomato"]
    company_factor = 0.75 if company.lower().strip() in faang else 1.0

    raw = (base_risk * 0.40 + day_factor * 0.45) * company_factor
    risk = min(max(raw, 0.05), 0.97)

    # Best day to apply (Tuesday has ~2x response rate)
    today = datetime.today()
    days_until_tuesday = (1 - today.weekday()) % 7
    best_day = (today + timedelta(days=days_until_tuesday)).strftime("%A, %B %d")

    risk_level = "Low" if risk < 0.35 else "Medium" if risk < 0.65 else "High"
    risk_color = "#10b981" if risk_level == "Low" else "#f59e0b" if risk_level == "Medium" else "#ef4444"

    return {
        "score": round(risk * 100),
        "level": risk_level,
        "color": risk_color,
        "best_day_to_apply": best_day,
        "followup_trigger_days": 10 if risk > 0.50 else 14,
        "breakdown": {
            "department_base": round(base_risk * 100),
            "days_factor": round(day_factor * 100),
            "company_factor": "FAANG (lower risk)" if company_factor < 1 else "Standard",
        },
        "tip": f"Apply on Tuesday for ~2× response rate. If no reply after {10 if risk > 0.50 else 14} days, BridgeFi will auto-draft a follow-up.",
    }


# ---------------------------------------------------------------------------
# Claude AI Integration
# ---------------------------------------------------------------------------
def call_claude(prompt: str, system: str = "") -> str:
    """Call Claude claude-sonnet-4-20250514 API. Falls back to mock if no key."""
    if not ANTHROPIC_API_KEY:
        return None  # Will trigger mock fallback

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        messages = [{"role": "user", "content": prompt}]
        kwargs = {"model": "claude-sonnet-4-20250514", "max_tokens": 1500, "messages": messages}
        if system:
            kwargs["system"] = system
        response = client.messages.create(**kwargs)
        return response.content[0].text
    except Exception as e:
        app.logger.error(f"Claude API error: {e}")
        return None


def analyze_skill_gap_mock(jd_text: str, user_skills: str) -> dict:
    """Return realistic mock skill-gap analysis when no API key is set."""
    return {
        "required_skills": [
            {"skill": "Python (FastAPI / Django)", "priority": "Critical", "your_level": "Check profile"},
            {"skill": "SQL & Database Design", "priority": "High", "your_level": "Check profile"},
            {"skill": "Docker & Kubernetes", "priority": "High", "your_level": "Potential gap"},
            {"skill": "System Design (Distributed)", "priority": "Medium", "your_level": "Potential gap"},
            {"skill": "REST & GraphQL APIs", "priority": "Medium", "your_level": "Check profile"},
            {"skill": "CI/CD Pipelines", "priority": "Low", "your_level": "Potential gap"},
        ],
        "hidden_signals": [
            "Team likely uses microservices — Kubernetes experience is implicit requirement",
            "Startup stage suggests high ownership — mention side projects prominently",
            "Referral keywords detected: 'fast-paced', 'ownership', 'impact'",
            "Implicit seniority signal: 3+ years implied despite not stated",
            "Cultural fit: collaborative, agile, no-ego engineering culture",
        ],
        "artifact_project": {
            "title": "Mini-Project: Skill Bridge Artifact",
            "description": "Build a FastAPI CRUD service with PostgreSQL, Docker, and a GitHub Actions CI pipeline. This demonstrates your top 3 skill gaps in a single runnable project.",
            "estimated_time": "90 minutes",
            "github_template": "https://github.com/bridgefi/artifact-template",
            "steps": [
                "Set up FastAPI app with SQLAlchemy ORM",
                "Add Docker + docker-compose.yml",
                "Write basic tests with pytest",
                "Add GitHub Actions workflow",
                "Deploy to Railway / Render (free tier)",
            ],
        },
        "match_score": 62,
        "recommendation": "You match ~62% of explicit requirements. Close the Docker/K8s gap with the artifact above to reach 80%+ competitiveness.",
        "best_apply_day": "Tuesday",
    }


def parse_claude_skill_gap(raw: str, jd_text: str) -> dict:
    """Parse Claude's JSON response for skill-gap analysis."""
    try:
        # Strip markdown fences if present
        clean = raw.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception:
        return analyze_skill_gap_mock(jd_text, "")


# ---------------------------------------------------------------------------
# Routes — Pages
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    """Landing page."""
    stats = {
        "apps": Application.query.count(),
        "candidates": Candidate.query.count(),
        "ghosted": Application.query.filter_by(status="Ghosted").count(),
        "offers": Application.query.filter_by(status="Offer").count(),
    }
    return render_template("index.html", stats=stats)


@app.route("/applicant")
def applicant_dashboard():
    """Applicant dashboard — job tracker + insights."""
    apps = Application.query.order_by(Application.applied_date.desc()).all()
    total = len(apps)
    active = sum(1 for a in apps if a.status in ("Applied", "Interview"))
    offers = sum(1 for a in apps if a.status == "Offer")
    ghosted = sum(1 for a in apps if a.status == "Ghosted")
    avg_risk = round(sum(a.ghosting_risk for a in apps) / total * 100) if total else 0

    status_counts = {
        "Applied": sum(1 for a in apps if a.status == "Applied"),
        "Interview": sum(1 for a in apps if a.status == "Interview"),
        "Offer": sum(1 for a in apps if a.status == "Offer"),
        "Ghosted": sum(1 for a in apps if a.status == "Ghosted"),
        "Rejected": sum(1 for a in apps if a.status == "Rejected"),
    }

    return render_template(
        "applicant.html",
        applications=apps,
        total=total, active=active, offers=offers,
        ghosted=ghosted, avg_risk=avg_risk,
        status_counts=json.dumps(status_counts),
    )


@app.route("/recruiter")
def recruiter_dashboard():
    """Recruiter dashboard — candidate pipeline."""
    candidates = Candidate.query.order_by(Candidate.applied_date.desc()).all()
    total = len(candidates)
    shortlisted = sum(1 for c in candidates if c.status == "Shortlisted")
    interviews = sum(1 for c in candidates if c.status == "Interview")
    hired = sum(1 for c in candidates if c.status == "Hired")
    pending_response = sum(1 for c in candidates if not c.response_sent)
    avg_skill = round(sum(c.skill_score for c in candidates) / total * 100) if total else 0

    status_counts = {
        "Under Review": sum(1 for c in candidates if c.status == "Under Review"),
        "Shortlisted": sum(1 for c in candidates if c.status == "Shortlisted"),
        "Interview": sum(1 for c in candidates if c.status == "Interview"),
        "Hired": sum(1 for c in candidates if c.status == "Hired"),
        "Rejected": sum(1 for c in candidates if c.status == "Rejected"),
    }

    return render_template(
        "recruiter.html",
        candidates=candidates,
        total=total, shortlisted=shortlisted, interviews=interviews,
        hired=hired, pending_response=pending_response, avg_skill=avg_skill,
        status_counts=json.dumps(status_counts),
    )


@app.route("/analyzer")
def skill_analyzer():
    """Skill-gap artifact generator page."""
    return render_template("analyzer.html")


@app.route("/profile-intelligence")
def profile_intelligence():
    """Personal Dashboard — Profile Intelligence Engine."""
    return render_template("profile_intelligence.html")


# ---------------------------------------------------------------------------
# API Routes — Applications (Applicant)
# ---------------------------------------------------------------------------
@app.route("/api/applications", methods=["GET"])
def get_applications():
    apps = Application.query.order_by(Application.applied_date.desc()).all()
    return jsonify([a.to_dict() for a in apps])


@app.route("/api/applications", methods=["POST"])
def add_application():
    data = request.get_json(force=True)
    if not data or not data.get("company") or not data.get("role"):
        return jsonify({"error": "company and role are required"}), 400

    applied_date_str = data.get("applied_date", "")
    applied_date = datetime.now()
    if applied_date_str:
        try:
            applied_date = datetime.strptime(applied_date_str, "%Y-%m-%d")
        except ValueError:
            pass

    days_since = (datetime.now() - applied_date).days
    risk_data = calculate_ghosting_risk(
        data["company"], data["role"],
        data.get("department", "Engineering"), days_since
    )

    app_obj = Application(
        company=data["company"],
        role=data["role"],
        department=data.get("department", "Engineering"),
        status=data.get("status", "Applied"),
        applied_date=applied_date,
        notes=data.get("notes", ""),
        job_url=data.get("job_url", ""),
        ghosting_risk=risk_data["score"] / 100,
    )
    db.session.add(app_obj)
    db.session.commit()
    return jsonify(app_obj.to_dict()), 201


@app.route("/api/applications/<int:app_id>", methods=["PATCH"])
def update_application(app_id):
    app_obj = db.session.get(Application, app_id)
    if not app_obj:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(force=True)
    for field in ("company", "role", "department", "status", "notes", "job_url"):
        if field in data:
            setattr(app_obj, field, data[field])
    if "follow_up_sent" in data:
        app_obj.follow_up_sent = data["follow_up_sent"]
    app_obj.last_updated = datetime.utcnow()
    db.session.commit()
    return jsonify(app_obj.to_dict())


@app.route("/api/applications/<int:app_id>", methods=["DELETE"])
def delete_application(app_id):
    app_obj = db.session.get(Application, app_id)
    if not app_obj:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(app_obj)
    db.session.commit()
    return jsonify({"deleted": True})


# ---------------------------------------------------------------------------
# API Routes — Ghosting Prediction
# ---------------------------------------------------------------------------
@app.route("/api/ghosting-risk", methods=["POST"])
def ghosting_risk_api():
    data = request.get_json(force=True)
    company = data.get("company", "Unknown")
    role = data.get("role", "Engineer")
    department = data.get("department", "Engineering")
    days = int(data.get("days_since_apply", 0))
    result = calculate_ghosting_risk(company, role, department, days)
    return jsonify(result)


# ---------------------------------------------------------------------------
# API Routes — Skill-Gap Analyzer
# ---------------------------------------------------------------------------
@app.route("/api/analyze-jd", methods=["POST"])
def analyze_jd():
    data = request.get_json(force=True)
    jd_text = data.get("jd_text", "").strip()
    user_skills = data.get("user_skills", "").strip()

    if not jd_text:
        return jsonify({"error": "jd_text is required"}), 400

    system_prompt = (
        "You are BridgeFi's skill-gap intelligence engine. "
        "Analyze the job description and return ONLY a JSON object with this exact structure:\n"
        "{\n"
        "  \"required_skills\": [{\"skill\": string, \"priority\": \"Critical|High|Medium|Low\", \"your_level\": string}],\n"
        "  \"hidden_signals\": [string],\n"
        "  \"artifact_project\": {\"title\": string, \"description\": string, \"estimated_time\": string, \"steps\": [string]},\n"
        "  \"match_score\": integer (0-100),\n"
        "  \"recommendation\": string,\n"
        "  \"best_apply_day\": \"Tuesday\"\n"
        "}\n"
        "hidden_signals should uncover 5 implicit/unstated requirements not directly written in the JD. "
        "artifact_project should be a concrete mini-project that bridges the top skill gaps. "
        "Return ONLY valid JSON, no markdown, no preamble."
    )

    user_prompt = (
        f"Job Description:\n{jd_text}\n\n"
        f"Candidate's Current Skills (may be empty):\n{user_skills or 'Not provided'}\n\n"
        "Analyze and return the JSON."
    )

    raw = call_claude(user_prompt, system_prompt)
    if raw:
        result = parse_claude_skill_gap(raw, jd_text)
    else:
        result = analyze_skill_gap_mock(jd_text, user_skills)

    # Persist result
    record = SkillGapResult(jd_text=jd_text, user_skills=user_skills, result_json=json.dumps(result))
    db.session.add(record)
    db.session.commit()

    return jsonify(result)


# ---------------------------------------------------------------------------
# API Routes — Follow-up Generator
# ---------------------------------------------------------------------------
@app.route("/api/generate-followup", methods=["POST"])
def generate_followup():
    data = request.get_json(force=True)
    company = data.get("company", "the company")
    role = data.get("role", "the position")
    applied_date = data.get("applied_date", "recently")
    tone = data.get("tone", "professional")

    prompt = (
        f"Generate a concise, {tone} follow-up email for a job application.\n"
        f"Company: {company}\nRole: {role}\nApplied on: {applied_date}\n"
        "Keep it under 120 words. Subject line + body. Be genuine, not pushy. "
        "End with a clear CTA asking for next steps."
    )

    raw = call_claude(prompt)
    if raw:
        email_text = raw.strip()
    else:
        email_text = (
            f"Subject: Follow-up on {role} Application — [Your Name]\n\n"
            f"Hi [Recruiter's Name],\n\n"
            f"I wanted to follow up on my application for the {role} position at {company} "
            f"submitted on {applied_date}. I remain very excited about the opportunity and "
            f"believe my skills align strongly with your team's needs.\n\n"
            "Could you please share an update on the hiring timeline? "
            "I'd love to discuss how I can contribute to the team.\n\n"
            "Thank you for your time.\n\nBest regards,\n[Your Name]"
        )

    # Mark follow-up sent if app_id provided
    app_id = data.get("app_id")
    if app_id:
        app_obj = db.session.get(Application, int(app_id))
        if app_obj:
            app_obj.follow_up_sent = True
            db.session.commit()

    return jsonify({"email": email_text})


# ---------------------------------------------------------------------------
# API Routes — Candidates (Recruiter)
# ---------------------------------------------------------------------------
@app.route("/api/candidates", methods=["GET"])
def get_candidates():
    candidates = Candidate.query.order_by(Candidate.applied_date.desc()).all()
    return jsonify([c.to_dict() for c in candidates])


@app.route("/api/candidates", methods=["POST"])
def add_candidate():
    data = request.get_json(force=True)
    if not data or not data.get("name") or not data.get("email"):
        return jsonify({"error": "name and email are required"}), 400

    candidate = Candidate(
        name=data["name"],
        email=data["email"],
        role=data.get("role", ""),
        status=data.get("status", "Under Review"),
        skill_score=float(data.get("skill_score", 0)) / 100,
        honesty_score=float(data.get("honesty_score", 0)) / 100,
        notes=data.get("notes", ""),
    )
    db.session.add(candidate)
    db.session.commit()
    return jsonify(candidate.to_dict()), 201


@app.route("/api/candidates/<int:cid>", methods=["PATCH"])
def update_candidate(cid):
    candidate = db.session.get(Candidate, cid)
    if not candidate:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(force=True)
    for field in ("name", "email", "role", "status", "notes"):
        if field in data:
            setattr(candidate, field, data[field])
    if "skill_score" in data:
        candidate.skill_score = float(data["skill_score"]) / 100
    if "honesty_score" in data:
        candidate.honesty_score = float(data["honesty_score"]) / 100
    if "response_sent" in data:
        candidate.response_sent = data["response_sent"]
    db.session.commit()
    return jsonify(candidate.to_dict())


@app.route("/api/candidates/<int:cid>", methods=["DELETE"])
def delete_candidate(cid):
    candidate = db.session.get(Candidate, cid)
    if not candidate:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(candidate)
    db.session.commit()
    return jsonify({"deleted": True})


@app.route("/api/bulk-followup", methods=["POST"])
def bulk_followup():
    """Mark all pending candidates as responded (one-click bulk follow-up)."""
    pending = Candidate.query.filter_by(response_sent=False).all()
    count = len(pending)
    for c in pending:
        c.response_sent = True
    db.session.commit()
    return jsonify({"updated": count, "message": f"Status update sent to {count} candidates."})


# ---------------------------------------------------------------------------
# API Routes — Stats / Analytics
# ---------------------------------------------------------------------------
@app.route("/api/stats")
def get_stats():
    apps = Application.query.all()
    candidates = Candidate.query.all()

    total_apps = len(apps)
    ghosted_apps = sum(1 for a in apps if a.status == "Ghosted")
    ghosting_rate = round(ghosted_apps / total_apps * 100) if total_apps else 0

    return jsonify({
        "applicant": {
            "total_applications": total_apps,
            "active": sum(1 for a in apps if a.status in ("Applied", "Interview")),
            "offers": sum(1 for a in apps if a.status == "Offer"),
            "ghosted": ghosted_apps,
            "ghosting_rate": ghosting_rate,
            "avg_risk": round(sum(a.ghosting_risk for a in apps) / total_apps * 100) if total_apps else 0,
        },
        "recruiter": {
            "total_candidates": len(candidates),
            "shortlisted": sum(1 for c in candidates if c.status == "Shortlisted"),
            "hired": sum(1 for c in candidates if c.status == "Hired"),
            "pending_response": sum(1 for c in candidates if not c.response_sent),
            "avg_skill_score": round(sum(c.skill_score for c in candidates) / len(candidates) * 100) if candidates else 0,
        },
    })


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_database()
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
