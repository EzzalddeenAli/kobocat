# coding: utf-8
from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy
from ...models import Instance


class Command(BaseCommand):
    help = gettext_lazy("Relink all instances with the current forms.")

    def handle(self, *args, **kwargs):
        for instance in Instance.objects.all():
            instance._link()
            instance.save()
