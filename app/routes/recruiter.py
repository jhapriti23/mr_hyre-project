from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user
from sqlalchemy import func

from app.extensions import db
from app.forms import ApplicationStatusForm, JobForm, ProfileForm
from app.models import Application, Job
from app.services.matching_service import analyze_job_posting, rank_applications_for_job
from app.utils.decorators import recruiter_required

recruiter_bp = Blueprint("recruiter", __name__)


@recruiter_bp.route("/dashboard")
@recruiter_required
def dashboard():
    jobs = (
        Job.query.filter_by(recruiter_id=current_user.id)
        .order_by(Job.created_at.desc())
        .all()
    )
    job_ids = [j.id for j in jobs]
    total_applications = (
        Application.query.filter(Application.job_id.in_(job_ids)).count()
        if job_ids
        else 0
    )
    shortlisted = (
        Application.query.filter(
            Application.job_id.in_(job_ids),
            Application.status == "shortlisted",
        ).count()
        if job_ids
        else 0
    )
    avg_match = (
        db.session.query(func.avg(Application.match_score))
        .filter(Application.job_id.in_(job_ids))
        .scalar()
        if job_ids
        else 0
    )

    recent_applications = (
        Application.query.join(Job)
        .filter(Job.recruiter_id == current_user.id)
        .order_by(Application.applied_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "recruiter/dashboard.html",
        jobs=jobs,
        stats={
            "total_jobs": len(jobs),
            "open_jobs": sum(1 for j in jobs if j.status == "open"),
            "total_applications": total_applications,
            "shortlisted": shortlisted,
            "avg_match": round(avg_match or 0, 1),
        },
        recent_applications=recent_applications,
    )


@recruiter_bp.route("/jobs/new", methods=["GET", "POST"])
@recruiter_required
def create_job():
    form = JobForm()
    if not form.company.data and current_user.company:
        form.company.data = current_user.company

    if form.validate_on_submit():
        job = Job(
            recruiter_id=current_user.id,
            title=form.title.data.strip(),
            company=form.company.data.strip(),
            location=form.location.data.strip() if form.location.data else None,
            employment_type=form.employment_type.data,
            salary_range=form.salary_range.data.strip()
            if form.salary_range.data
            else None,
            description=form.description.data.strip(),
            requirements=form.requirements.data.strip()
            if form.requirements.data
            else None,
        )
        db.session.add(job)
        db.session.commit()

        analyze_job_posting(job)
        flash("Job posted and analyzed by AI successfully.", "success")
        return redirect(url_for("recruiter.view_job", job_id=job.id))

    return render_template("recruiter/job_form.html", form=form, title="Post New Job")


@recruiter_bp.route("/jobs/<int:job_id>")
@recruiter_required
def view_job(job_id):
    job = Job.query.filter_by(id=job_id, recruiter_id=current_user.id).first_or_404()
    applications = rank_applications_for_job(job.id)
    status_form = ApplicationStatusForm()
    return render_template(
        "recruiter/job_detail.html",
        job=job,
        applications=applications,
        status_form=status_form,
    )


@recruiter_bp.route("/jobs/<int:job_id>/edit", methods=["GET", "POST"])
@recruiter_required
def edit_job(job_id):
    job = Job.query.filter_by(id=job_id, recruiter_id=current_user.id).first_or_404()
    form = JobForm(obj=job)

    if form.validate_on_submit():
        job.title = form.title.data.strip()
        job.company = form.company.data.strip()
        job.location = form.location.data.strip() if form.location.data else None
        job.employment_type = form.employment_type.data
        job.salary_range = (
            form.salary_range.data.strip() if form.salary_range.data else None
        )
        job.description = form.description.data.strip()
        job.requirements = (
            form.requirements.data.strip() if form.requirements.data else None
        )
        db.session.commit()
        analyze_job_posting(job)
        flash("Job updated and re-analyzed by AI.", "success")
        return redirect(url_for("recruiter.view_job", job_id=job.id))

    return render_template(
        "recruiter/job_form.html", form=form, title="Edit Job", job=job
    )


@recruiter_bp.route("/jobs/<int:job_id>/close", methods=["POST"])
@recruiter_required
def close_job(job_id):
    job = Job.query.filter_by(id=job_id, recruiter_id=current_user.id).first_or_404()
    job.status = "closed"
    db.session.commit()
    flash("Job closed.", "info")
    return redirect(url_for("recruiter.view_job", job_id=job.id))


@recruiter_bp.route("/jobs/<int:job_id>/reopen", methods=["POST"])
@recruiter_required
def reopen_job(job_id):
    job = Job.query.filter_by(id=job_id, recruiter_id=current_user.id).first_or_404()
    job.status = "open"
    db.session.commit()
    flash("Job reopened.", "success")
    return redirect(url_for("recruiter.view_job", job_id=job.id))


@recruiter_bp.route(
    "/jobs/<int:job_id>/applications/<int:app_id>/status", methods=["POST"]
)
@recruiter_required
def update_application_status(job_id, app_id):
    job = Job.query.filter_by(id=job_id, recruiter_id=current_user.id).first_or_404()
    application = Application.query.filter_by(id=app_id, job_id=job.id).first_or_404()
    form = ApplicationStatusForm()

    if form.validate_on_submit():
        application.status = form.status.data
        db.session.commit()
        flash("Application status updated.", "success")

    return redirect(url_for("recruiter.view_job", job_id=job.id))


@recruiter_bp.route("/applications/<int:app_id>")
@recruiter_required
def view_application(app_id):
    application = (
        Application.query.join(Job)
        .filter(
            Application.id == app_id,
            Job.recruiter_id == current_user.id,
        )
        .first_or_404()
    )
    status_form = ApplicationStatusForm(status=application.status)
    return render_template(
        "recruiter/application_detail.html",
        application=application,
        status_form=status_form,
    )


@recruiter_bp.route("/profile", methods=["GET", "POST"])
@recruiter_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data.strip()
        current_user.phone = form.phone.data.strip() if form.phone.data else None
        current_user.company = (
            form.company.data.strip() if form.company.data else None
        )
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("recruiter.profile"))

    return render_template("recruiter/profile.html", form=form)
