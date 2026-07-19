#!/usr/bin/env python
"""
شغل الملف ده على السيرفر الأونلاين:
    python fix_online_slugs.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartoffer_django.settings')
django.setup()

from django.utils.text import slugify
from core.models import Company

print('Companies count:', Company.objects.count())

for c in Company.objects.all():
    old = c.slug
    if not c.slug:
        base = slugify(c.name, allow_unicode=True)
        s = base
        n = 1
        while Company.objects.filter(slug=s).exclude(pk=c.pk).exists():
            s = f'{base}-{n}'
            n += 1
        c.slug = s
        c.save(update_fields=['slug'])
        print(f'Fixed: {c.name} -> {c.slug}')
    else:
        print(f'OK: {c.name} -> {c.slug}')

print('Done!')
