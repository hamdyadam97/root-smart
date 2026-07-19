from django.core.management.base import BaseCommand
from accounts.utils import generate_permissions


class Command(BaseCommand):
    help = 'Generate CRUD permissions for all project models'

    def handle(self, *args, **options):
        created = generate_permissions()
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created} new permissions'))
