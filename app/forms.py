from flask_wtf import FlaskForm
from wtforms import (
    EmailField,
    FileField,
    HiddenField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError

from app.models import User


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign In")


class RegisterForm(FlaskForm):
    full_name = StringField(
        "Full Name", validators=[DataRequired(), Length(min=2, max=120)]
    )
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=8, max=128)]
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    role = SelectField(
        "I am a",
        choices=[("candidate", "Candidate"), ("recruiter", "Recruiter")],
        validators=[DataRequired()],
    )
    company = StringField("Company", validators=[Optional(), Length(max=120)])
    phone = StringField("Phone", validators=[Optional(), Length(max=20)])
    submit = SubmitField("Create Account")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError("An account with this email already exists.")


class JobForm(FlaskForm):
    title = StringField("Job Title", validators=[DataRequired(), Length(max=200)])
    company = StringField("Company", validators=[DataRequired(), Length(max=120)])
    location = StringField("Location", validators=[Optional(), Length(max=120)])
    employment_type = SelectField(
        "Employment Type",
        choices=[
            ("Full-time", "Full-time"),
            ("Part-time", "Part-time"),
            ("Contract", "Contract"),
            ("Internship", "Internship"),
            ("Remote", "Remote"),
        ],
        default="Full-time",
    )
    salary_range = StringField("Salary Range", validators=[Optional(), Length(max=100)])
    description = TextAreaField(
        "Job Description", validators=[DataRequired(), Length(min=50)]
    )
    requirements = TextAreaField("Requirements", validators=[Optional()])
    submit = SubmitField("Post Job")


class ResumeUploadForm(FlaskForm):
    resume = FileField("Upload Resume", validators=[DataRequired()])
    submit = SubmitField("Upload & Parse")


class ApplicationForm(FlaskForm):
    cover_letter = TextAreaField("Cover Letter (optional)", validators=[Optional()])
    submit = SubmitField("Apply Now")


class ApplicationStatusForm(FlaskForm):
    status = SelectField(
        "Status",
        choices=[
            ("applied", "Applied"),
            ("reviewing", "Reviewing"),
            ("shortlisted", "Shortlisted"),
            ("rejected", "Rejected"),
            ("hired", "Hired"),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Update Status")


class ProfileForm(FlaskForm):
    full_name = StringField(
        "Full Name", validators=[DataRequired(), Length(min=2, max=120)]
    )
    phone = StringField("Phone", validators=[Optional(), Length(max=20)])
    company = StringField("Company", validators=[Optional(), Length(max=120)])
    submit = SubmitField("Save Profile")
