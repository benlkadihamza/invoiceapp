from flask import Blueprint, render_template
from flask_login import login_required
from models import db, Transaction, Person
from sqlalchemy import func
from datetime import date

statistics_bp = Blueprint('statistics', __name__)


@statistics_bp.route('/statistics')
@login_required
def index():
    today = date.today()
    month = today.month
    year = today.year

    largest_expense = db.session.query(Transaction).filter(
        Transaction.expense > 0
    ).order_by(Transaction.expense.desc()).first()

    largest_income = db.session.query(Transaction).filter(
        Transaction.income > 0
    ).order_by(Transaction.income.desc()).first()

    from sqlalchemy import extract

    days_with_transactions = db.session.query(func.count(func.distinct(Transaction.date))).scalar() or 1
    total_expenses = db.session.query(func.coalesce(func.sum(Transaction.expense), 0.0)).scalar() or 0.0
    avg_daily_spending = float(total_expenses) / max(days_with_transactions, 1)

    total_month_expense = db.session.query(func.coalesce(func.sum(Transaction.expense), 0.0)).filter(
        extract('month', Transaction.date) == month,
        extract('year', Transaction.date) == year,
        Transaction.expense > 0).scalar() or 0.0
    total_month_income = db.session.query(func.coalesce(func.sum(Transaction.income), 0.0)).filter(
        extract('month', Transaction.date) == month,
        extract('year', Transaction.date) == year,
        Transaction.income > 0).scalar() or 0.0

    months_with_data = db.session.query(func.count(func.distinct(
        func.concat(extract('year', Transaction.date), '-', extract('month', Transaction.date))
    ))).scalar() or 1
    avg_monthly_spending = float(total_expenses) / max(months_with_data, 1)

    persons = db.session.query(
        Person.name,
        func.count(Transaction.id).label('count')
    ).join(Transaction, Transaction.person_id == Person.id
    ).group_by(Person.id).order_by(func.count(Transaction.id).desc()).all()

    most_active_person = persons[0] if persons else None

    return render_template('statistics.html',
                           largest_expense=largest_expense,
                           largest_income=largest_income,
                           avg_daily_spending=avg_daily_spending,
                           avg_monthly_spending=avg_monthly_spending,
                           most_active_person=most_active_person,
                           persons=persons,
                           total_income=float(total_month_income),
                           total_expense=float(total_month_expense))
