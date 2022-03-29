# coding: utf-8
from django.conf import settings
from django.utils.translation import gettext as t
from rest_framework import exceptions

from onadata.apps.main.models.user_profile import UserProfile


class MFABlockerMixin:

    def validate_mfa_not_active(self, user: 'auth.User'):
        """
        Raise an exception if MFA is enabled for user's account.
        """

        # This condition is kind of temporary. We can activate/deactivate
        # class based on settings. Useful until we decide whether
        # TokenAuthentication should be deactivated with MFA
        # ToDo Remove the condition when kobotoolbox/kpi#3383 is released/merged
        class_path = f'{self.__module__}.{self.__class__.__name__}'
        if class_path not in settings.MFA_SUPPORTED_AUTH_CLASSES:
            try:
                is_mfa_active = user.profile.is_mfa_active
            except UserProfile.DoesNotExist:
                pass
            else:
                if is_mfa_active:
                    raise exceptions.AuthenticationFailed(t(
                        'Multi-factor authentication is enabled for this '
                        'account. ##authentication class## cannot be used.'
                    ).replace('##authentication class##', self.verbose_name))
