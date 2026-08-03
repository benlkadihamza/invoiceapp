import os
import time
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app, session
from flask_login import login_required, current_user
from models import db, MonthlyBackup
from forms import RestoreDatabaseForm
from idempotency import idempotent_route

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

FRENCH_MONTHS = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
    5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
    9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
}


def get_db_path():
    uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if uri.startswith('sqlite:///'):
        db_path = uri.replace('sqlite:///', '')
        if not os.path.isabs(db_path):
            db_path = os.path.join(current_app.root_path, db_path)
        return db_path
    return os.path.join(current_app.root_path, 'database', 'app.db')


@settings_bp.route('/')
@login_required
def index():
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    current_french = f"{FRENCH_MONTHS.get(current_month, 'Mois')} {current_year}"
    last_backup = MonthlyBackup.query.filter_by(completed=True).order_by(MonthlyBackup.year.desc(), MonthlyBackup.month.desc(), MonthlyBackup.id.desc()).first()
    current_backup = MonthlyBackup.query.filter_by(month=current_month, year=current_year, completed=True).first()
    is_up_to_date = bool(current_backup)

    restore_form = RestoreDatabaseForm()

    return render_template(
        'settings.html',
        last_backup=last_backup,
        current_backup=current_backup,
        is_up_to_date=is_up_to_date,
        current_french_month_year=current_french,
        current_month=current_month,
        current_year=current_year,
        restore_form=restore_form
    )


@settings_bp.route('/backup/download', methods=['GET', 'POST'])
@login_required
def download_backup():
    now = datetime.now()
    override_month = request.args.get('month', type=int)
    override_year = request.args.get('year', type=int)

    month = override_month if override_month else now.month
    year = override_year if override_year else now.year

    french_month = FRENCH_MONTHS.get(month, "Mois")
    filename = f"{french_month} {year}.db"

    username = current_user.username if (current_user and current_user.is_authenticated) else 'admin'

    try:
        record = MonthlyBackup.query.filter_by(month=month, year=year).first()
        if not record:
            record = MonthlyBackup(
                month=month,
                year=year,
                filename=filename,
                downloaded_at=datetime.utcnow(),
                downloaded_by=username,
                completed=True
            )
            db.session.add(record)
        else:
            record.filename = filename
            record.downloaded_at = datetime.utcnow()
            record.downloaded_by = username
            record.completed = True

        db.session.commit()
    except Exception as e:
        db.session.rollback()

    session.pop('backup_snooze_until', None)
    session.pop('backup_dismissed_month', None)

    db_path = get_db_path()
    if not os.path.exists(db_path):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        with open(db_path, 'wb') as f:
            f.write(b'')

    return send_file(
        db_path,
        as_attachment=True,
        download_name=filename,
        mimetype='application/x-sqlite3'
    )


@settings_bp.route('/backup/restore', methods=['POST'])
@login_required
@idempotent_route(redirect_endpoint='settings.index')
def restore_backup():
    form = RestoreDatabaseForm()
    if form.validate_on_submit():
        file = form.database_file.data
        if file and file.filename.lower().endswith('.db'):
            try:
                db_path = get_db_path()
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                db.session.remove()
                file.save(db_path)
                flash('Base de données restaurée avec succès.', 'success')
            except Exception as e:
                flash(f'Erreur lors de la restauration: {str(e)}', 'danger')
        else:
            flash('Format de fichier invalide. Veuillez sélectionner un fichier .db', 'danger')
    else:
        for field, errors in form.errors.items():
            for err in errors:
                flash(f'Erreur: {err}', 'danger')

    return redirect(url_for('settings.index'))


@settings_bp.route('/backup/snooze', methods=['GET', 'POST'])
@login_required
def snooze_reminder():
    session['backup_snooze_until'] = time.time() + 86400  # 24 hours
    flash('Rappel de sauvegarde reporté à demain (24h).', 'info')
    return redirect(request.referrer or url_for('dashboard.index'))


@settings_bp.route('/backup/dismiss', methods=['GET', 'POST'])
@login_required
def dismiss_reminder():
    now = datetime.now()
    session['backup_dismissed_month'] = f"{now.year}_{now.month}"
    flash('Rappel ignoré pour cette session.', 'info')
    return redirect(request.referrer or url_for('dashboard.index'))


@settings_bp.route('/toggle-decimals', methods=['POST'])
@login_required
def toggle_decimals():
    show_decimals = request.form.get('show_decimals') == 'on'
    current_user.show_decimals = show_decimals
    db.session.commit()
    status_str = "activé (.00)" if show_decimals else "désactivé (sans .00)"
    flash(f"Affichage des décimales {status_str}.", "success")
    return redirect(url_for('settings.index'))


@settings_bp.route('/toggle-daily-totals', methods=['POST'])
@login_required
def toggle_daily_totals():
    show_daily_totals = request.form.get('show_daily_totals') == 'on'
    current_user.show_daily_totals = show_daily_totals
    db.session.commit()
    status_str = "affichés dans le PDF" if show_daily_totals else "masqués (par défaut)"
    flash(f"Totaux quotidiens dans le PDF mensuel : {status_str}.", "success")
    return redirect(url_for('settings.index'))


