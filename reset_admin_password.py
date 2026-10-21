#!/usr/bin/env python3
"""
Script de réinitialisation du mot de passe administrateur pour l'application FinanceApp.
Usage:
    python reset_admin_password.py [NOUVEAU_MOT_DE_PASSE]
    python reset_admin_password.py -u admin -p newpassword
"""

import sys
import argparse
import getpass
from app import create_app
from models import db, User


def reset_admin_password(username="admin", new_password=None):
    """
    Réinitialise le mot de passe de l'utilisateur spécifié.
    Crée l'utilisateur s'il n'existe pas.
    """
    if not new_password:
        raise ValueError("Le nouveau mot de passe ne peut pas être vide.")

    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"Utilisateur '{username}' introuvable. Création de l'utilisateur...")
            user = User(username=username)
            db.session.add(user)

        user.set_password(new_password)
        db.session.commit()
        print(f"Le mot de passe pour l'utilisateur '{username}' a été réinitialisé avec succès.")
        return True


def main():
    parser = argparse.ArgumentParser(description="Réinitialiser le mot de passe administrateur")
    parser.add_argument("password_arg", nargs="?", help="Nouveau mot de passe (optionnel)")
    parser.add_argument("-u", "--username", default="admin", help="Nom d'utilisateur (par défaut: admin)")
    parser.add_argument("-p", "--password", help="Nouveau mot de passe")

    args = parser.parse_args()

    password = args.password or args.password_arg

    if not password:
        try:
            password = getpass.getpass(f"Entrez le nouveau mot de passe pour '{args.username}': ")
            if not password:
                print("Erreur: Le mot de passe ne peut pas être vide.", file=sys.stderr)
                sys.exit(1)
            confirm_password = getpass.getpass("Confirmez le nouveau mot de passe: ")
            if password != confirm_password:
                print("Erreur: Les mots de passe ne correspondent pas.", file=sys.stderr)
                sys.exit(1)
        except (KeyboardInterrupt, EOFError):
            print("\nOpération annulée.")
            sys.exit(1)

    if not password.strip():
        print("Erreur: Le mot de passe ne peut pas être vide.", file=sys.stderr)
        sys.exit(1)

    try:
        success = reset_admin_password(username=args.username, new_password=password)
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"Erreur lors de la réinitialisation: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
