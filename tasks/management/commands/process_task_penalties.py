from django.core.management.base import BaseCommand

from tasks.services import process_penalties


class Command(BaseCommand):
    help = 'احتساب خصومات المهام (التأخير وعدم التعليق) حتى أمس — يُشغَّل يوميًا عبر cron.'

    def handle(self, *args, **options):
        created = process_penalties()
        self.stdout.write(self.style.SUCCESS(f'تم إنشاء {len(created)} خصم جديد.'))
