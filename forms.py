from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, PasswordField, TextAreaField, FloatField,
                     SelectField, DateField, SubmitField, HiddenField, BooleanField)
from wtforms.validators import DataRequired, Optional, Email, Length, EqualTo, ValidationError
from models import User


class LoginForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    remember_me = BooleanField('Se souvenir de moi')
    submit = SubmitField('Se connecter')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Mot de passe actuel', validators=[DataRequired()])
    new_password = PasswordField('Nouveau mot de passe', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmer le mot de passe',
                                     validators=[DataRequired(), EqualTo('new_password', message='Les mots de passe ne correspondent pas.')])
    submit = SubmitField('Changer le mot de passe')


class TransactionForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    person_id = SelectField('Personne', coerce=int, validators=[DataRequired()])
    payment_method_id = SelectField('Mode de paiement', coerce=int, validators=[Optional()])
    description = StringField('Description', validators=[DataRequired(), Length(max=200)])
    income = FloatField('Revenu (DH)', validators=[Optional()])
    expense = FloatField('Dépense (DH)', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    receipt = FileField('Reçu', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Images et PDF uniquement.')])
    submit = SubmitField('Enregistrer')


class PersonForm(FlaskForm):
    name = StringField('Nom', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Téléphone', validators=[Optional(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Enregistrer')


class ReportFilterForm(FlaskForm):
    date_from = DateField('Du', validators=[Optional()], format='%Y-%m-%d')
    date_to = DateField('Au', validators=[Optional()], format='%Y-%m-%d')
    person_id = SelectField('Personne', coerce=int, validators=[Optional()], choices=[(0, 'Toutes')])
    submit = SubmitField('Filtrer')


class RestoreDatabaseForm(FlaskForm):
    database_file = FileField('Fichier de sauvegarde (.db)', validators=[DataRequired(), FileAllowed(['db'], 'Fichiers .db uniquement.')])
    submit = SubmitField('Restaurer la base de données (.db)')
