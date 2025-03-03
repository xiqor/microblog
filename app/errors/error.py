from flask import render_template, Blueprint, current_app

bp = Blueprint('errors', __name__)

@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@bp.app_errorhandler(500)
def internal_error(error):
    with current_app.app_context():
        from app import db
        db.session.rollback()
    return render_template('500.html'), 500