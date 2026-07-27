from flask import Blueprint, render_template
from flask_login import login_required
from models import db, Transaction
from sqlalchemy import func, extract
from datetime import date, datetime

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    today = date.today()
    current_month = today.month
    current_year = today.year

    total_income = db.session.query(func.coalesce(func.sum(Transaction.income), 0.0)).scalar()
    total_expense = db.session.query(func.coalesce(func.sum(Transaction.expense), 0.0)).scalar()
    current_balance = total_income - total_expense

    today_income = db.session.query(func.coalesce(func.sum(Transaction.income), 0.0)).filter(
        Transaction.date == today, Transaction.income > 0).scalar()
    today_expense = db.session.query(func.coalesce(func.sum(Transaction.expense), 0.0)).filter(
        Transaction.date == today, Transaction.expense > 0).scalar()

    month_income = db.session.query(func.coalesce(func.sum(Transaction.income), 0.0)).filter(
        extract('month', Transaction.date) == current_month,
        extract('year', Transaction.date) == current_year,
        Transaction.income > 0).scalar()
    month_expense = db.session.query(func.coalesce(func.sum(Transaction.expense), 0.0)).filter(
        extract('month', Transaction.date) == current_month,
        extract('year', Transaction.date) == current_year,
        Transaction.expense > 0).scalar()

    year_income = db.session.query(func.coalesce(func.sum(Transaction.income), 0.0)).filter(
        extract('year', Transaction.date) == current_year,
        Transaction.income > 0).scalar()
    year_expense = db.session.query(func.coalesce(func.sum(Transaction.expense), 0.0)).filter(
        extract('year', Transaction.date) == current_year,
        Transaction.expense > 0).scalar()

    monthly_net = month_income - month_expense

    months = []
    monthly_income_data = []
    monthly_expense_data = []
    for m in range(1, 13):
        mi = db.session.query(func.coalesce(func.sum(Transaction.income), 0.0)).filter(
            extract('month', Transaction.date) == m,
            extract('year', Transaction.date) == current_year,
            Transaction.income > 0).scalar()
        me = db.session.query(func.coalesce(func.sum(Transaction.expense), 0.0)).filter(
            extract('month', Transaction.date) == m,
            extract('year', Transaction.date) == current_year,
            Transaction.expense > 0).scalar()
        months.append(datetime(2026, m, 1).strftime('%b'))
        monthly_income_data.append(float(mi))
        monthly_expense_data.append(float(me))

    daily_dates = []
    daily_balance = []
    running = float(current_balance)
    for day in range(1, today.day + 1):
        d = date(current_year, current_month, day)
        day_income = float(db.session.query(func.coalesce(func.sum(Transaction.income), 0.0)).filter(
            Transaction.date == d, Transaction.income > 0).scalar() or 0)
        day_expense = float(db.session.query(func.coalesce(func.sum(Transaction.expense), 0.0)).filter(
            Transaction.date == d, Transaction.expense > 0).scalar() or 0)
        daily_dates.append(d.strftime('%d/%m'))
        daily_balance.append(running)
        running = running - day_income + day_expense
        running = running + day_income - day_expense
        daily_balance[-1] = running

    prev_year_income = db.session.query(func.coalesce(func.sum(Transaction.income), 0.0)).filter(
        extract('year', Transaction.date) == current_year - 1,
        Transaction.income > 0).scalar()
    prev_year_expense = db.session.query(func.coalesce(func.sum(Transaction.expense), 0.0)).filter(
        extract('year', Transaction.date) == current_year - 1,
        Transaction.expense > 0).scalar()

    recent_transactions = Transaction.query.order_by(Transaction.date.desc(), Transaction.id.desc()).limit(10).all()
    transactions_with_balance = _compute_running_balance(recent_transactions)

    from models import InvoicePayment
    from routes.payments import sync_invoice_payments
    sync_invoice_payments()

    payments_pending = InvoicePayment.query.filter_by(status='Pending').count()
    payments_partial = InvoicePayment.query.filter_by(status='Partial').count()
    payments_paid = InvoicePayment.query.filter_by(status='Paid').count()
    all_pm = InvoicePayment.query.all()
    total_remaining_amount = sum(p.remaining_amount for p in all_pm)
    total_collected_amount = sum(p.total_paid for p in all_pm)

    return render_template('dashboard.html',
                           current_balance=current_balance,
                           total_income=total_income, total_expense=total_expense,
                           today_income=today_income, today_expense=today_expense,
                           month_income=month_income, month_expense=month_expense,
                           year_income=year_income, year_expense=year_expense,
                           monthly_net=monthly_net,
                           months=months, monthly_income_data=monthly_income_data,
                           monthly_expense_data=monthly_expense_data,
                           daily_dates=daily_dates, daily_balance=daily_balance,
                           prev_year_income=prev_year_income, prev_year_expense=prev_year_expense,
                           recent_transactions=transactions_with_balance,
                           payments_pending=payments_pending,
                           payments_partial=payments_partial,
                           payments_paid=payments_paid,
                           total_remaining_amount=total_remaining_amount,
                           total_collected_amount=total_collected_amount)


def _compute_running_balance(transactions):
    all_txns = Transaction.query.order_by(Transaction.date.asc(), Transaction.id.asc()).all()
    balance = 0.0
    balance_map = {}
    for t in all_txns:
        balance += t.income - t.expense
        balance_map[t.id] = balance
    result = []
    for t in transactions:
        result.append({'transaction': t, 'balance': balance_map.get(t.id, 0)})
    return result
