from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required
from models import db, Transaction, Person, PaymentMethod
from forms import TransactionForm
from werkzeug.utils import secure_filename
from datetime import date
import os, uuid

transactions_bp = Blueprint('transactions', __name__)


def _get_all_balance_map():
    all_txns = Transaction.query.order_by(Transaction.date.asc(), Transaction.id.asc()).all()
    balance = 0.0
    balance_map = {}
    for t in all_txns:
        balance += t.income - t.expense
        balance_map[t.id] = balance
    return balance_map


@transactions_bp.route('/transactions')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    query = Transaction.query

    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    person_id = request.args.get('person_id', 0, type=int)
    payment_method_id = request.args.get('payment_method_id', 0, type=int)
    search = request.args.get('search', '')
    month = request.args.get('month', 0, type=int)
    year = request.args.get('year', 0, type=int)

    if date_from:
        try:
            query = query.filter(Transaction.date >= date.fromisoformat(date_from))
        except ValueError:
            pass
    if date_to:
        try:
            query = query.filter(Transaction.date <= date.fromisoformat(date_to))
        except ValueError:
            pass
    if person_id:
        query = query.filter(Transaction.person_id == person_id)
    if payment_method_id:
        query = query.filter(Transaction.payment_method_id == payment_method_id)
    if month:
        from sqlalchemy import extract
        query = query.filter(extract('month', Transaction.date) == month)
    if year:
        from sqlalchemy import extract
        query = query.filter(extract('year', Transaction.date) == year)
    if search:
        from sqlalchemy import or_
        query = query.filter(or_(
            Transaction.description.ilike(f'%{search}%'),
            Transaction.notes.ilike(f'%{search}%'),
            Transaction.person.has(Person.name.ilike(f'%{search}%')),
        ))

    pagination = query.order_by(Transaction.date.desc(), Transaction.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False)

    balance_map = _get_all_balance_map()
    transactions_with_balance = []
    for t in pagination.items:
        transactions_with_balance.append({'transaction': t, 'balance': balance_map.get(t.id, 0)})

    persons = Person.query.order_by(Person.name).all()
    payment_methods = PaymentMethod.query.order_by(PaymentMethod.name).all()

    total_income = sum(t.income for t in pagination.items)
    total_expense = sum(t.expense for t in pagination.items)

    return render_template('transactions.html',
                           transactions=transactions_with_balance,
                           pagination=pagination, persons=persons,
                           payment_methods=payment_methods,
                           total_income=total_income, total_expense=total_expense,
                           filters={
                               'date_from': date_from, 'date_to': date_to,
                               'person_id': person_id, 'search': search,
                               'payment_method_id': payment_method_id,
                               'month': month, 'year': year, 'per_page': per_page,
                           })


from idempotency import idempotent_route


@transactions_bp.route('/transactions/add', methods=['GET', 'POST'])
@login_required
@idempotent_route(redirect_endpoint='transactions.index')
def add():
    form = TransactionForm()
    if not form.date.data:
        form.date.data = date.today()
    form.person_id.choices = [(0, '-- Sélectionner une personne --')] + [(p.id, p.name) for p in Person.query.order_by(Person.name).all()]
    form.payment_method_id.choices = [(0, '-- Aucun --')] + [(pm.id, pm.name) for pm in PaymentMethod.query.order_by(PaymentMethod.name).all()]

    if form.validate_on_submit():
        try:
            receipt_filename = None
            if form.receipt.data:
                ext = form.receipt.data.filename.rsplit('.', 1)[1].lower()
                receipt_filename = f"{uuid.uuid4().hex}.{ext}"
                form.receipt.data.save(os.path.join(current_app.config['UPLOAD_FOLDER'], receipt_filename))

            income_val = form.income.data or 0.0
            expense_val = form.expense.data or 0.0

            t = Transaction(
                date=form.date.data,
                description=form.description.data,
                income=income_val,
                expense=expense_val,
                notes=form.notes.data,
                receipt_image=receipt_filename,
                person_id=form.person_id.data,
                payment_method_id=form.payment_method_id.data if form.payment_method_id.data else None,
            )

            db.session.add(t)
            db.session.commit()
            flash('Transaction ajoutée avec succès.', 'success')
            return redirect(url_for('transactions.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de l\'ajout de la transaction : {str(e)}', 'danger')
            return redirect(url_for('transactions.index'))

    return render_template('transaction_form.html', form=form, title='Ajouter une transaction')


@transactions_bp.route('/transactions/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@idempotent_route(redirect_endpoint='transactions.index')
def edit(id):
    t = Transaction.query.get_or_404(id)
    form = TransactionForm(obj=t)
    if request.method == 'GET':
        if not form.income.data:
            form.income.data = None
        if not form.expense.data:
            form.expense.data = None
    form.person_id.choices = [(0, '-- Sélectionner une personne --')] + [(p.id, p.name) for p in Person.query.order_by(Person.name).all()]
    form.payment_method_id.choices = [(0, '-- Aucun --')] + [(pm.id, pm.name) for pm in PaymentMethod.query.order_by(PaymentMethod.name).all()]

    if form.validate_on_submit():
        try:
            if form.receipt.data:
                ext = form.receipt.data.filename.rsplit('.', 1)[1].lower()
                receipt_filename = f"{uuid.uuid4().hex}.{ext}"
                form.receipt.data.save(os.path.join(current_app.config['UPLOAD_FOLDER'], receipt_filename))
                t.receipt_image = receipt_filename

            income_val = form.income.data or 0.0
            expense_val = form.expense.data or 0.0

            t.date = form.date.data
            t.description = form.description.data
            t.person_id = form.person_id.data
            t.payment_method_id = form.payment_method_id.data if form.payment_method_id.data else None
            t.notes = form.notes.data
            t.income = income_val
            t.expense = expense_val

            db.session.commit()
            flash('Transaction modifiée avec succès.', 'success')
            return redirect(url_for('transactions.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification de la transaction : {str(e)}', 'danger')
            return redirect(url_for('transactions.index'))

    return render_template('transaction_form.html', form=form, title='Modifier la transaction')


@transactions_bp.route('/transactions/duplicate/<int:id>')
@login_required
@idempotent_route(redirect_endpoint='transactions.index')
def duplicate(id):
    original = Transaction.query.get_or_404(id)
    try:
        t = Transaction(
            date=date.today(),
            description=original.description + ' (copie)',
            income=original.income,
            expense=original.expense,
            notes=original.notes,
            person_id=original.person_id,
            payment_method_id=original.payment_method_id,
        )
        db.session.add(t)
        db.session.commit()
        flash('Transaction dupliquée avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la duplication de la transaction : {str(e)}', 'danger')
    return redirect(url_for('transactions.index'))


@transactions_bp.route('/transactions/delete/<int:id>', methods=['POST'])
@login_required
@idempotent_route(redirect_endpoint='transactions.index')
def delete(id):
    t = Transaction.query.get_or_404(id)
    try:
        if t.receipt_image:
            path = os.path.join(current_app.config['UPLOAD_FOLDER'], t.receipt_image)
            if os.path.exists(path):
                os.remove(path)
        db.session.delete(t)
        db.session.commit()
        flash('Transaction supprimée.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression : {str(e)}', 'danger')
    return redirect(url_for('transactions.index'))
