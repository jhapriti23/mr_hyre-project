from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)  # recruiter | candidate
    company = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    jobs = db.relationship("Job", backref="recruiter", lazy="dynamic")
    resume = db.relationship("Resume", backref="candidate", uselist=False)
    applications = db.relationship("Application", backref="candidate", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_recruiter(self):
        return self.role == "recruiter"

    @property
    def is_candidate(self):
        return self.role == "candidate"

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    recruiter_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120))
    employment_type = db.Column(db.String(50), default="Full-time")
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    salary_range = db.Column(db.String(100))
    status = db.Column(db.String(20), default="open", index=True)  # open | closed
    ai_analysis = db.Column(db.Text)
    ai_skills = db.Column(db.Text)
    ai_experience_level = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    applications = db.relationship(
        "Application", backref="job", lazy="dynamic", cascade="all, delete-orphan"
    )

    @property
    def skills_list(self):
        if not self.ai_skills:
            return []
        return [s.strip() for s in self.ai_skills.split(",") if s.strip()]

    def __repr__(self):
        return f"<Job {self.title}>"


class Resume(db.Model):
    __tablename__ = "resumes"

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False
    )
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    raw_text = db.Column(db.Text)
    parsed_name = db.Column(db.String(120))
    parsed_email = db.Column(db.String(120))
    parsed_phone = db.Column(db.String(20))
    parsed_skills = db.Column(db.Text)
    parsed_experience = db.Column(db.Text)
    parsed_education = db.Column(db.Text)
    parsed_summary = db.Column(db.Text)
    ai_summary = db.Column(db.Text)
    uploaded_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    @property
    def skills_list(self):
        if not self.parsed_skills:
            return []
        return [s.strip() for s in self.parsed_skills.split(",") if s.strip()]

    def __repr__(self):
        return f"<Resume candidate_id={self.candidate_id}>"


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(
        db.Integer, db.ForeignKey("jobs.id"), nullable=False, index=True
    )
    candidate_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    status = db.Column(
        db.String(30), default="applied", index=True
    )  # applied | reviewing | shortlisted | rejected | hired
    cover_letter = db.Column(db.Text)
    match_score = db.Column(db.Float, default=0.0)
    match_analysis = db.Column(db.Text)
    match_strengths = db.Column(db.Text)
    match_gaps = db.Column(db.Text)
    applied_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint("job_id", "candidate_id", name="uq_job_candidate"),
    )

    @property
    def strengths_list(self):
        if not self.match_strengths:
            return []
        return [s.strip() for s in self.match_strengths.split("|") if s.strip()]

    @property
    def gaps_list(self):
        if not self.match_gaps:
            return []
        return [s.strip() for s in self.match_gaps.split("|") if s.strip()]

    def __repr__(self):
        return f"<Application job={self.job_id} candidate={self.candidate_id}>"
