from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Backfill missing slugs for all models that use slug-based URLs'

    def handle(self, *args, **options):
        models = [
            ('offers', 'StudentOffer'),
            ('finance', 'Payment'),
            ('finance', 'Call'),
            ('registrations', 'Account'),
            ('reports', 'ReportSnapshot'),
            ('students', 'Student'),
        ]

        total_updated = 0
        for app_label, model_name in models:
            Model = self.get_model(app_label, model_name)
            qs = Model.objects.filter(slug__isnull=True) | Model.objects.filter(slug='')
            count = qs.count()
            if count:
                self.stdout.write(f'Updating {count} {app_label}.{model_name} records...')
                for instance in qs.iterator():
                    instance.save()
                total_updated += count
            else:
                self.stdout.write(f'{app_label}.{model_name}: all good')

        self.stdout.write(self.style.SUCCESS(f'Done. Total records updated: {total_updated}'))

    def get_model(self, app_label, model_name):
        from django.apps import apps
        return apps.get_model(app_label, model_name)
