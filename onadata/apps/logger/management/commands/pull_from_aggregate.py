#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 fileencoding=utf-8
# coding: utf-8
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as t

from onadata.libs.utils.briefcase_client import BriefcaseClient


class Command(BaseCommand):
    help = t("Insert all existing parsed instances into MongoDB")

    def add_arguments(self, parser):
        parser.add_argument('--url',
                            help=t("server url to pull forms and submissions"))

        parser.add_argument('-u', '--username',
                            help=t("Username"))

        parser.add_argument('-p', '--password',
                            help=t("Password"))

        parser.add_argument('--to',
                            help=t("username in this server"))

    def handle(self, *args, **kwargs):
        url = kwargs.get('url')
        username = kwargs.get('username')
        password = kwargs.get('password')
        to = kwargs.get('to')
        user = User.objects.get(username=to)
        bc = BriefcaseClient(username=username, password=password,
                             user=user, url=url)
        bc.download_xforms(include_instances=True)
