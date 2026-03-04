import os
from django.core.management.base import BaseCommand, CommandError
from apps.users.models import BaseUser

class Command(BaseCommand):
    help = "Créer un superutilisateur s'il n'existe pas, en utilisant ADMIN_EMAIL et ADMIN_PASSWORD."

    def handle(self, *args, **options):
        email = os.environ.get("ADMIN_EMAIL")
        password = os.environ.get("ADMIN_PASSWORD")

        if not email or not password:
            raise CommandError("Veuillez définir les variables d'environnement ADMIN_EMAIL et ADMIN_PASSWORD.")

        if BaseUser.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f"Un utilisateur avec l'email {email} existe déjà."))
        else:
            BaseUser.objects.create_superuser(email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"Superutilisateur {email} créé avec succès."))
