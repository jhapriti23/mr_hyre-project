import uuid
from pathlib import Path

from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Application
from app.services.gemini_service import GeminiService
from app.services.resume_parser import extract_text_from_file


def allowed_file(filename, allowed_extensions):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in allowed_extensions
    )


def save_resume_file(file_storage, upload_folder):
    original = secure_filename(file_storage.filename)
    ext = original.rsplit(".", 1)[-1].lower()
    stored_name = f"{uuid.uuid4().hex}.{ext}"
    dest = Path(upload_folder) / stored_name
    file_storage.save(dest)
    return stored_name, original, str(dest)


def process_resume_upload(resume_record, file_path):
    raw_text = extract_text_from_file(file_path)
    resume_record.raw_text = raw_text

    gemini = GeminiService()
    parsed = gemini.parse_resume(raw_text)

    resume_record.parsed_name = parsed.get("parsed_name", "")
    resume_record.parsed_email = parsed.get("parsed_email", "")
    resume_record.parsed_phone = parsed.get("parsed_phone", "")
    resume_record.parsed_skills = parsed.get("parsed_skills", "")
    resume_record.parsed_experience = parsed.get("parsed_experience", "")
    resume_record.parsed_education = parsed.get("parsed_education", "")
    resume_record.parsed_summary = parsed.get("parsed_summary", "")
    resume_record.ai_summary = parsed.get("ai_summary", "")

    return resume_record


def compute_match_for_application(application):
    job = application.job
    candidate = application.candidate
    resume = candidate.resume

    if not resume or not resume.raw_text:
        application.match_score = 0.0
        application.match_analysis = "No resume on file for matching."
        return application

    gemini = GeminiService()
    match_data = gemini.match_candidate_to_job(job, resume)

    application.match_score = match_data["match_score"]
    application.match_analysis = match_data["match_analysis"]
    application.match_strengths = match_data["match_strengths"]
    application.match_gaps = match_data["match_gaps"]
    return application


def rank_applications_for_job(job_id):
    applications = (
        Application.query.filter_by(job_id=job_id)
        .order_by(Application.match_score.desc())
        .all()
    )
    return applications


def analyze_job_posting(job):
    gemini = GeminiService()
    result = gemini.analyze_job(
        job.title,
        job.description,
        job.requirements or "",
    )
    job.ai_analysis = result["analysis"]
    job.ai_skills = result["skills"]
    job.ai_experience_level = result["experience_level"]
    db.session.commit()
    return job
