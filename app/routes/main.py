from flask import Blueprint, render_template
from flask_login import current_user

from app.models import Job

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    recent_jobs = (
        Job.query.filter_by(status="open")
        .order_by(Job.created_at.desc())
        .limit(6)
        .all()
    )
    stats = {
        "open_jobs": Job.query.filter_by(status="open").count(),
        "total_jobs": Job.query.count(),
    }
    return render_template(
        "main/index.html",
        recent_jobs=recent_jobs,
        stats=stats,
        current_user=current_user,
    )


@main_bp.route("/jobs")
def jobs_list():
    jobs = Job.query.filter_by(status="open").order_by(Job.created_at.desc()).all()
    return render_template("main/jobs.html", jobs=jobs)


@main_bp.route("/jobs/<int:job_id>")
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template("main/job_detail.html", job=job)
