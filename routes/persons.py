from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models import db, Person
from forms import PersonForm
from idempotency import idempotent_route

persons_bp = Blueprint('persons', __name__)


@persons_bp.route('/persons')
@login_required
def index():
    persons = Person.query.order_by(Person.name).all()
    return render_template('persons.html', persons=persons)


@persons_bp.route('/persons/add', methods=['GET', 'POST'])
@login_required
@idempotent_route(redirect_endpoint='persons.index')
def add():
    form = PersonForm()
    if form.validate_on_submit():
        try:
            p = Person(
                name=form.name.data,
                phone=form.phone.data,
                email=form.email.data,
                notes=form.notes.data,
            )
            db.session.add(p)
            db.session.commit()
            flash('Personne ajoutée avec succès.', 'success')
            return redirect(url_for('persons.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de l\'ajout de la personne : {str(e)}', 'danger')
            return redirect(url_for('persons.index'))
    return render_template('person_form.html', form=form, title='Ajouter une personne')


@persons_bp.route('/persons/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@idempotent_route(redirect_endpoint='persons.index')
def edit(id):
    p = Person.query.get_or_404(id)
    form = PersonForm(obj=p)
    if form.validate_on_submit():
        try:
            p.name = form.name.data
            p.phone = form.phone.data
            p.email = form.email.data
            p.notes = form.notes.data
            db.session.commit()
            flash('Personne modifiée avec succès.', 'success')
            return redirect(url_for('persons.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification de la personne : {str(e)}', 'danger')
            return redirect(url_for('persons.index'))
    return render_template('person_form.html', form=form, title='Modifier la personne')


@persons_bp.route('/persons/delete/<int:id>', methods=['POST'])
@login_required
@idempotent_route(redirect_endpoint='persons.index')
def delete(id):
    p = Person.query.get_or_404(id)
    if p.transactions.count() > 0:
        flash('Impossible de supprimer cette personne car elle a des transactions.', 'danger')
        return redirect(url_for('persons.index'))
    try:
        db.session.delete(p)
        db.session.commit()
        flash('Personne supprimée.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression : {str(e)}', 'danger')
    return redirect(url_for('persons.index'))


@persons_bp.route('/persons/<int:id>')
@login_required
def detail(id):
    p = Person.query.get_or_404(id)
    return render_template('person_detail.html', person=p)
