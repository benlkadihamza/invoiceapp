from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from models import db, PaymentMethod, TransactionDescription
from idempotency import idempotent_route

categories_bp = Blueprint('categories', __name__)


def _normalize_positions():
    descriptions = TransactionDescription.query.order_by(
        TransactionDescription.sort_order.asc(),
        TransactionDescription.id.asc()
    ).all()
    changed = False
    for idx, d in enumerate(descriptions, start=1):
        if d.sort_order != idx or d.position != idx:
            d.sort_order = idx
            d.position = idx
            changed = True
    if changed:
        db.session.commit()
    return descriptions


@categories_bp.route('/categories')
@login_required
def index():
    payment_methods = PaymentMethod.query.order_by(PaymentMethod.name).all()
    descriptions = _normalize_positions()
    return render_template('categories.html', payment_methods=payment_methods, descriptions=descriptions)


@categories_bp.route('/payment-methods/add', methods=['POST'])
@login_required
@idempotent_route(redirect_endpoint='categories.index')
def add_payment_method():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Le nom du mode de paiement est requis.', 'danger')
        return redirect(url_for('categories.index'))
    if PaymentMethod.query.filter_by(name=name).first():
        flash('Ce mode de paiement existe déjà.', 'warning')
        return redirect(url_for('categories.index'))
    try:
        pm = PaymentMethod(name=name)
        db.session.add(pm)
        db.session.commit()
        flash('Mode de paiement ajouté.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de l\'ajout du mode de paiement : {str(e)}', 'danger')
    return redirect(url_for('categories.index'))


@categories_bp.route('/payment-methods/delete/<int:id>', methods=['POST'])
@login_required
@idempotent_route(redirect_endpoint='categories.index')
def delete_payment_method(id):
    pm = PaymentMethod.query.get_or_404(id)
    if pm.transactions.count() > 0:
        flash('Impossible de supprimer ce mode de paiement car il est utilisé.', 'danger')
        return redirect(url_for('categories.index'))
    try:
        db.session.delete(pm)
        db.session.commit()
        flash('Mode de paiement supprimé.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression : {str(e)}', 'danger')
    return redirect(url_for('categories.index'))


@categories_bp.route('/categories/descriptions/add', methods=['POST'])
@login_required
@idempotent_route(redirect_endpoint='categories.index')
def add_description():
    name = request.form.get('name', '').strip()
    if not name:
        flash('La description est requise.', 'danger')
        return redirect(url_for('categories.index'))
    existing = TransactionDescription.query.filter(
        db.func.lower(TransactionDescription.name) == db.func.lower(name)
    ).first()
    if existing:
        flash('Cette description existe déjà.', 'warning')
        return redirect(url_for('categories.index'))
    try:
        max_order = db.session.query(db.func.max(TransactionDescription.sort_order)).scalar() or 0
        td = TransactionDescription(name=name, sort_order=max_order + 1, position=max_order + 1)
        db.session.add(td)
        db.session.commit()
        flash('Description ajoutée avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de l\'ajout de la description : {str(e)}', 'danger')
    return redirect(url_for('categories.index'))


@categories_bp.route('/categories/descriptions/edit/<int:id>', methods=['POST'])
@login_required
@idempotent_route(redirect_endpoint='categories.index')
def edit_description(id):
    td = TransactionDescription.query.get_or_404(id)
    name = request.form.get('name', '').strip()
    if not name:
        flash('La description est requise.', 'danger')
        return redirect(url_for('categories.index'))
    existing = TransactionDescription.query.filter(
        db.func.lower(TransactionDescription.name) == db.func.lower(name),
        TransactionDescription.id != id
    ).first()
    if existing:
        flash('Une autre description porte déjà ce nom.', 'warning')
        return redirect(url_for('categories.index'))
    try:
        td.name = name
        db.session.commit()
        flash('Description modifiée avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la modification de la description : {str(e)}', 'danger')
    return redirect(url_for('categories.index'))


@categories_bp.route('/categories/descriptions/delete/<int:id>', methods=['POST'])
@login_required
@idempotent_route(redirect_endpoint='categories.index')
def delete_description(id):
    td = TransactionDescription.query.get_or_404(id)
    try:
        db.session.delete(td)
        db.session.commit()
        _normalize_positions()
        flash('Description supprimée.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression de la description : {str(e)}', 'danger')
    return redirect(url_for('categories.index'))


@categories_bp.route('/categories/descriptions/reorder', methods=['POST'])
@login_required
def reorder_descriptions():
    data = request.get_json(silent=True) or {}
    order_list = data.get('order') or []
    if not order_list or not isinstance(order_list, list):
        return jsonify({'success': False, 'message': 'Données d\'ordre invalides.'}), 400

    submitted_ids = [item.get('id') for item in order_list if isinstance(item, dict) and 'id' in item]
    if len(submitted_ids) != len(set(submitted_ids)):
        return jsonify({'success': False, 'message': 'Identifiants en double dans la demande.'}), 400

    all_existing = TransactionDescription.query.all()
    existing_ids = {d.id for d in all_existing}

    if not set(submitted_ids).issubset(existing_ids):
        return jsonify({'success': False, 'message': 'L\'ordre soumis contient des identifiants inconnus.'}), 400

    try:
        desc_map = {d.id: d for d in all_existing}
        for item in order_list:
            desc_id = item.get('id')
            new_order = int(item.get('sort_order', 0))
            if desc_id in desc_map:
                desc_map[desc_id].sort_order = new_order
                desc_map[desc_id].position = new_order
        db.session.commit()
        _normalize_positions()
        return jsonify({'success': True, 'message': 'Ordre enregistré avec succès.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erreur lors de l\'enregistrement de l\'ordre : {str(e)}'}), 500



