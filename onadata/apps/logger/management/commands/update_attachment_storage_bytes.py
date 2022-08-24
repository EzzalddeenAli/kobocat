from __future__ import annotations

import json
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum

from onadata.apps.logger.models.attachment import Attachment
from onadata.apps.logger.models.instance import Instance
from onadata.apps.logger.models.xform import XForm
from onadata.apps.main.models.user_profile import UserProfile
from onadata.libs.utils.jsonbfield_helper import ReplaceValues


class Command(BaseCommand):
    help = (
        'Retroactively calculate the total attachment file storage '
        'per xform and user profile'
    )

    def handle(self, *args, **kwargs):
        self.verbosity = kwargs['verbosity']

        # Dictionary which contains the total of bytes for each user. Useful
        # to avoid another aggregate query on attachments to calculate users
        # global usage.
        total_per_user = defaultdict(int)

        # Release any locks on the users' profile from getting submissions
        UserProfile.objects.exclude(
            metadata__attachments_counting_status='complete'
        ).update(
            metadata=ReplaceValues(
                'metadata',
                updates={'submissions_suspended': False},
            ),
        )

        # Get all profiles already updated to exclude their forms from the list
        up_queryset = UserProfile.objects.values_list('user_id', flat=True).filter(
            metadata__attachments_counting_status='complete'
        )
        # Get only xforms whose users' storage counters have not been updated yet
        xforms = (
            XForm.objects.exclude(user_id__in=up_queryset)
            .values('pk', 'user_id', 'user__username')
            .order_by('user_id')
        )

        last_xform = None
        for xform in xforms:

            if not last_xform or (last_xform['user_id'] != xform['user_id']):
                # Retrieve or create user's profile.
                (
                    user_profile,
                    created,
                ) = UserProfile.objects.get_or_create(user_id=xform['user_id'])

                # Some old profiles don't have metadata
                if user_profile.metadata is None:
                    user_profile.metadata = {}

                # Set the flag to true if it was never set.
                if not user_profile.metadata.get('submissions_suspended'):
                    # We are using the flag `submissions_suspended` to prevent
                    # new submissions from coming in while the
                    # `attachment_storage_bytes` is being calculated.
                    user_profile.metadata['submissions_suspended'] = True
                    user_profile.save(update_fields=['metadata'])

                # if `last_xform` is not none, it means that the `user_id` is
                # different from the previous one in the loop so the user
                # profile must be updated
                if last_xform:
                    self.update_user_profile(
                        last_xform, total_per_user[last_xform['user_id']]
                    )

            # write out xform progress
            if self.verbosity >= 1:
                self.stdout.write(
                    f"Calculating attachments for xform_id #{xform['pk']}"
                    f" (user {xform['user__username']})"
                )
            # aggregate total media file size for all media per xform
            form_attachments = Attachment.objects.filter(
                instance__xform_id=xform['pk']
            ).aggregate(total=Sum('media_file_size'))

            if form_attachments['total']:
                with transaction.atomic():
                    if self.verbosity >= 1:
                        self.stdout.write(
                            f'\tUpdating xform attachment storage to '
                            f"{form_attachments['total']} bytes"
                        )

                    XForm.objects.filter(
                        pk=xform['pk']
                    ).update(
                        attachment_storage_bytes=form_attachments['total']
                    )

                total_per_user[xform['user_id']] += form_attachments['total']
            elif self.verbosity >= 1:
                self.stdout.write('\tNo attachments found')

            last_xform = xform

        # need to call `update_user_profile()` one more time outside the loop
        # because the last user profile will not be up-to-date otherwise
        if last_xform:
            self.update_user_profile(
                last_xform, total_per_user[last_xform['user_id']]
            )

        if self.verbosity >= 1:
            self.stdout.write('Done!')

    def update_user_profile(self, xform: dict, total: int):
        user_id = xform['user_id']
        username = xform['user__username']

        if self.verbosity >= 1:
            self.stdout.write(
                f'Updating attachment storage total ({total} bytes) on '
                f'{username}’s profile'
            )

        # Update user's profile (and lock the related row)
        with transaction.atomic():
            updates = {
                'submissions_suspended': False,
                'attachments_counting_status': 'complete',
            }
            UserProfile.objects.filter(
                user_id=user_id
            ).update(
                attachment_storage_bytes=total,
                metadata=ReplaceValues(
                    'metadata',
                    updates=updates,
                ),
            )
