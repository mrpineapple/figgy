import os
import sys

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.core.validators import validate_email
from django.core.management import call_command


class Command(BaseCommand):
    args = '<user@host.domain>'
    help = 'Deletes local SQLite3 db, creates superuser `user` with default password.'

    def handle(self, *args, **options):
        """ Remove SQLite database, create superuser with username as password"""

        if not settings.DATABASES['default']['ENGINE'].endswith('sqlite3'):
            print('Whoa, we only delete SQLite3 databases')
            sys.exit(1)

        if len(args) != 1:
            print('Args: {0}\n    {1}'.format(Command.args, Command.help))
            sys.exit(1)

        try:
            email = args[0]
            validate_email(email)
            username = email.split('@')[0]
        except ValidationError:
            print('Invalid email address')
            sys.exit(0)

        db_name = settings.DATABASES['default']['NAME']
        os.remove(db_name)

        call_command('syncdb', interactive=False)

        admin = User.objects.create_superuser(username, email, username)
        admin.save()
