from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user


def recruiter_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("auth.login"))
        if not current_user.is_recruiter:
            abort(403)
        return f(*args, **kwargs)

    return decorated


def candidate_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("auth.login"))
        if not current_user.is_candidate:
            abort(403)
        return f(*args, **kwargs)

    return decorated
