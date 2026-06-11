from pathlib import Path

from flask import Blueprint, current_app, flash, redirect, render_template, url_for
from flask_login import current_user

from app.extensions import db
from app.forms import ApplicationForm, ProfileForm, ResumeUploadForm
from app.models import Application, Job, Resume
from app.services.matching_service import (
    allowed_file,
    compute_match_for_application,
    process_resume_upload,
    save_resume_file,
)
from app.utils.decorators import candidate_required

candidate_bp = Blueprint("candidate", __name__)


@candidate_bp.route("/dashboard")
@candidate_required
def dashboard():
    applications = (
        Application.query.filter_by(candidate_id=current_user.id)
        .order_by(Application.applied_at.desc())
        .all()
    )
    resume = current_user.resume
    open_jobs = Job.query.filter_by(status="open").count()

    return render_template(
        "candidate/dashboard.html",
        applications=applications,
        resume=resume,
        stats={
            "total_applications": len(applications),
            "shortlisted": sum(1 for a in applications if a.status == "shortlisted"),
            "avg_match": round(
                sum(a.match_score for a in applications) / len(applications), 1
            )
            if applications
            else 0,
            "open_jobs": open_jobs,
        },
    )


@candidate_bp.route("/resume", methods=["GET", "POST"])
@candidate_required
def resume():
    form = ResumeUploadForm()
    resume_record = current_user.resume

    if form.validate_on_submit():
        file = form.resume.data
        if not allowed_file(
            file.filename, current_app.config["ALLOWED_EXTENSIONS"]
        ):
            flash("Invalid file type. Upload PDF, DOCX, DOC, or TXT.", "danger")
            return redirect(url_for("candidate.resume"))

        stored_name, original, file_path = save_resume_file(
            file, current_app.config["UPLOAD_FOLDER"]
        )

        if resume_record:
            old_path = Path(resume_record.file_path)
            if old_path.exists():
                old_path.unlink(missing_ok=True)
            resume_record.filename = stored_name
            resume_record.original_filename = original
            resume_record.file_path = file_path
        else:
            resume_record = Resume(
                candidate_id=current_user.id,
                filename=stored_name,
                original_filename=original,
                file_path=file_path,
            )
            db.session.add(resume_record)

        process_resume_upload(resume_record, file_path)
        db.session.commit()
        flash("Resume uploaded and parsed successfully.", "success")
        return redirect(url_for("candidate.resume"))

    return render_template(
        "candidate/resume.html", form=form, resume=resume_record
    )


@candidate_bp.route("/jobs")
@candidate_required
def browse_jobs():
    jobs = Job.query.filter_by(status="open").order_by(Job.created_at.desc()).all()
    applied_job_ids = {
        a.job_id
        for a in Application.query.filter_by(candidate_id=current_user.id).all()
    }
    return render_template(
        "candidate/jobs.html", jobs=jobs, applied_job_ids=applied_job_ids
    )


@candidate_bp.route("/jobs/<int:job_id>/apply", methods=["GET", "POST"])
@candidate_required
def apply_job(job_id):
    job = Job.query.filter_by(id=job_id, status="open").first_or_404()

    existing = Application.query.filter_by(
        job_id=job.id, candidate_id=current_user.id
    ).first()
    if existing:
        flash("You have already applied to this job.", "info")
        return redirect(url_for("candidate.application_detail", app_id=existing.id))

    if not current_user.resume:
        flash("Please upload your resume before applying.", "warning")
        return redirect(url_for("candidate.resume"))

    form = ApplicationForm()
    if form.validate_on_submit():
        application = Application(
            job_id=job.id,
            candidate_id=current_user.id,
            cover_letter=form.cover_letter.data.strip()
            if form.cover_letter.data
            else None,
        )
        compute_match_for_application(application)
        db.session.add(application)
        db.session.commit()
        flash(
            f"Application submitted! AI match score: {application.match_score}%",
            "success",
        )
        return redirect(url_for("candidate.application_detail", app_id=application.id))

    return render_template("candidate/apply.html", job=job, form=form)


@candidate_bp.route("/applications/<int:app_id>")
@candidate_required
def application_detail(app_id):
    application = Application.query.filter_by(
        id=app_id, candidate_id=current_user.id
    ).first_or_404()
    return render_template("candidate/application_detail.html", application=application)


@candidate_bp.route("/applications")
@candidate_required
def applications():
    apps = (
        Application.query.filter_by(candidate_id=current_user.id)
        .order_by(Application.applied_at.desc())
        .all()
    )
    return render_template("candidate/applications.html", applications=apps)


@candidate_bp.route("/profile", methods=["GET", "POST"])
@candidate_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data.strip()
        current_user.phone = form.phone.data.strip() if form.phone.data else None
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("candidate.profile"))

    return render_template("candidate/profile.html", form=form)
