# coding: utf-8
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.template.loader import get_template
from django.utils.translation import gettext as t, gettext_lazy

from templated_email import send_templated_mail


class Command(BaseCommand):
    help = gettext_lazy("Send an email to all formhub users")

    def add_arguments(self, parser):
        parser.add_argument("-m", "--message", dest="message", default=False)

    def handle(self, *args, **kwargs):
        message = kwargs.get('message')
        verbosity = kwargs.get('verbosity')
        get_template('templated_email/notice.email')
        if not message:
            raise CommandError(t('message must be included in kwargs'))
        # get all users
        users = User.objects.all()
        for user in users:
            name = user.get_full_name()
            if not name or len(name) == 0:
                name = user.email
            if verbosity:
                print(t('Emailing name: %(name)s, email: %(email)s')
                      % {'name': name, 'email': user.email})
            # send each email separately so users cannot see each other
            send_templated_mail(
                template_name='notice',
                from_email='noreply@formhub.org',
                recipient_list=[user.email],
                context={
                    'username': user.username,
                    'full_name': name,
                    'message': message
                },
            )
