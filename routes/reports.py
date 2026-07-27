from flask import Blueprint, render_template, request, send_file, Response
from flask_login import login_required
from models import db, Transaction, Person
from sqlalchemy import func, extract
from datetime import date, timedelta
from io import BytesIO

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/reports')
@login_required
def index():
    return render_template('reports.html')


@reports_bp.route('/reports/daily')
@login_required
def daily():
    selected_date = request.args.get('date')
    if selected_date:
        try:
            selected_date = date.fromisoformat(selected_date)
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()

    transactions = Transaction.query.filter(
        Transaction.date == selected_date
    ).order_by(Transaction.date.asc(), Transaction.id.asc()).all()

    total_income = sum(t.income for t in transactions)
    total_expense = sum(t.expense for t in transactions)
    net_balance = total_income - total_expense

    return render_template('report_daily.html',
                           transactions=transactions,
                           selected_date=selected_date,
                           total_income=total_income,
                           total_expense=total_expense,
                           net_balance=net_balance)


@reports_bp.route('/reports/monthly')
@login_required
def monthly():
    month = request.args.get('month', date.today().month, type=int)
    year = request.args.get('year', date.today().year, type=int)

    transactions = Transaction.query.filter(
        extract('month', Transaction.date) == month,
        extract('year', Transaction.date) == year
    ).order_by(Transaction.date.asc(), Transaction.id.asc()).all()

    total_income = sum(t.income for t in transactions)
    total_expense = sum(t.expense for t in transactions)
    net_profit = total_income - total_expense

    all_txns = Transaction.query.order_by(Transaction.date.asc(), Transaction.id.asc()).all()
    running = 0.0
    closing_balance = 0.0
    for t in all_txns:
        running += t.income - t.expense
        if t.date.year == year and t.date.month == month:
            closing_balance = running

    person_totals = {}
    for t in transactions:
        pname = t.person.name if t.person else 'Inconnu'
        if pname not in person_totals:
            person_totals[pname] = {'income': 0, 'expense': 0, 'net': 0}
        person_totals[pname]['income'] += t.income
        person_totals[pname]['expense'] += t.expense
        person_totals[pname]['net'] += t.income - t.expense

    months_list = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                   'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']

    return render_template('report_monthly.html',
                           transactions=transactions,
                           selected_month=month, selected_year=year,
                           total_income=total_income, total_expense=total_expense,
                           net_profit=net_profit, closing_balance=closing_balance,
                           person_totals=person_totals, months_list=months_list)


@reports_bp.route('/reports/person')
@login_required
def person():
    month = request.args.get('month', date.today().month, type=int)
    year = request.args.get('year', date.today().year, type=int)

    persons = Person.query.all()
    person_data = []
    for p in persons:
        income = db.session.query(func.coalesce(func.sum(Transaction.income), 0.0)).filter(
            Transaction.person_id == p.id,
            extract('month', Transaction.date) == month,
            extract('year', Transaction.date) == year).scalar()
        expense = db.session.query(func.coalesce(func.sum(Transaction.expense), 0.0)).filter(
            Transaction.person_id == p.id,
            extract('month', Transaction.date) == month,
            extract('year', Transaction.date) == year).scalar()
        count = Transaction.query.filter(
            Transaction.person_id == p.id,
            extract('month', Transaction.date) == month,
            extract('year', Transaction.date) == year).count()
        if income > 0 or expense > 0:
            person_data.append({'person': p, 'income': float(income),
                                'expense': float(expense), 'count': count})

    months_list = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                   'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']

    return render_template('report_person.html',
                           person_data=person_data,
                           selected_month=month, selected_year=year,
                           months_list=months_list)


@reports_bp.route('/reports/weekly')
@login_required
def weekly():
    today = date.today()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)

    transactions = Transaction.query.filter(
        Transaction.date >= start,
        Transaction.date <= end
    ).order_by(Transaction.date.asc(), Transaction.id.asc()).all()

    total_income = sum(t.income for t in transactions)
    total_expense = sum(t.expense for t in transactions)

    return render_template('report_weekly.html',
                           transactions=transactions,
                           start_date=start, end_date=end,
                           total_income=total_income,
                           total_expense=total_expense)


@reports_bp.route('/reports/yearly')
@login_required
def yearly():
    year = request.args.get('year', date.today().year, type=int)

    transactions = Transaction.query.filter(
        extract('year', Transaction.date) == year
    ).order_by(Transaction.date.asc(), Transaction.id.asc()).all()

    total_income = sum(t.income for t in transactions)
    total_expense = sum(t.expense for t in transactions)

    monthly_data = []
    for m in range(1, 13):
        mi = float(db.session.query(func.coalesce(func.sum(Transaction.income), 0.0)).filter(
            extract('month', Transaction.date) == m,
            extract('year', Transaction.date) == year,
            Transaction.income > 0).scalar() or 0)
        me = float(db.session.query(func.coalesce(func.sum(Transaction.expense), 0.0)).filter(
            extract('month', Transaction.date) == m,
            extract('year', Transaction.date) == year,
            Transaction.expense > 0).scalar() or 0)
        monthly_data.append({'month': m, 'income': mi, 'expense': me, 'net': mi - me})

    return render_template('report_yearly.html',
                           transactions=transactions,
                           selected_year=year,
                           total_income=total_income,
                           total_expense=total_expense,
                           monthly_data=monthly_data)


@reports_bp.route('/reports/monthly/<int:year>/<int:month>/pdf')
@login_required
def monthly_pdf(year, month):
    from pdf_generator import generate_monthly_pdf, MONTHS_FR
    pdf_bytes = generate_monthly_pdf(year, month)
    buf = BytesIO(pdf_bytes)
    buf.seek(0)
    month_name = MONTHS_FR[month]
    filename = f'Rapport_{month_name}_{year}.pdf'
    return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=filename)


@reports_bp.route('/reports/daily/<int:year>/<int:month>/<int:day>/pdf')
@login_required
def daily_pdf(year, month, day):
    from pdf_generator import generate_daily_pdf
    pdf_bytes = generate_daily_pdf(year, month, day)
    buf = BytesIO(pdf_bytes)
    buf.seek(0)
    filename = f'Rapport_Quotidien_{year}_{month:02d}_{day:02d}.pdf'
    return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=filename)


@reports_bp.route('/reports/weekly/<start>/<end>/pdf')
@login_required
def weekly_pdf(start, end):
    from pdf_generator import generate_weekly_pdf
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    pdf_bytes = generate_weekly_pdf(start_date, end_date)
    buf = BytesIO(pdf_bytes)
    buf.seek(0)
    filename = f'Rapport_Hebdomadaire_{start}_{end}.pdf'
    return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=filename)


@reports_bp.route('/reports/yearly/<int:year>/pdf')
@login_required
def yearly_pdf(year):
    from pdf_generator import generate_yearly_pdf
    pdf_bytes = generate_yearly_pdf(year)
    buf = BytesIO(pdf_bytes)
    buf.seek(0)
    filename = f'Rapport_Annuel_{year}.pdf'
    return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=filename)


@reports_bp.route('/reports/person/<int:year>/<int:month>/pdf')
@login_required
def person_pdf(year, month):
    from pdf_generator import generate_person_pdf, MONTHS_FR
    pdf_bytes = generate_person_pdf(year, month)
    buf = BytesIO(pdf_bytes)
    buf.seek(0)
    month_name = MONTHS_FR[month]
    filename = f'Rapport_Personnes_{month_name}_{year}.pdf'
    return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=filename)


@reports_bp.route('/export/pdf')
@login_required
def full_pdf():
    from pdf_generator import generate_full_pdf
    pdf_bytes = generate_full_pdf()
    buf = BytesIO(pdf_bytes)
    buf.seek(0)
    from datetime import datetime
    filename = f'Rapport_Financier_{datetime.now().strftime("%Y_%m")}.pdf'
    return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=filename)
