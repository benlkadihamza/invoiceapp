from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models import db, PaymentMethod

categories_bp = Blueprint('categories', __name__)


@categories_bp.route('/categories')
@login_required
def index():
    payment_methods = PaymentMethod.query.order_by(PaymentMethod.name).all()
    return render_template('categories.html', payment_methods=payment_methods)


@categories_bp.route('/payment-methods/add', methods=['POST'])
@login_required
def add_payment_method():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Le nom du mode de paiement est requis.', 'danger')
        return redirect(url_for('categories.index'))
    if PaymentMethod.query.filter_by(name=name).first():
        flash('Ce mode de paiement existe déjà.', 'warning')
        return redirect(url_for('categories.index'))
    pm = PaymentMethod(name=name)
    db.session.add(pm)
    db.session.commit()
    flash('Mode de paiement ajouté.', 'success')
    return redirect(url_for('categories.index'))


@categories_bp.route('/payment-methods/delete/<int:id>', methods=['POST'])
@login_required
def delete_payment_method(id):
    pm = PaymentMethod.query.get_or_404(id)
    if pm.transactions.count() > 0:
        flash('Impossible de supprimer ce mode de paiement car il est utilisé.', 'danger')
        return redirect(url_for('categories.index'))
    db.session.delete(pm)
    db.session.commit()
    flash('Mode de paiement supprimé.', 'success')
    return redirect(url_for('categories.index'))
