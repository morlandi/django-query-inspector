import os
import glob
import sys
import signal
import datetime
from pprint import pprint
from django.conf import settings
from django.core.management.base import BaseCommand


def get_source_folder():
    """
    Retrieve target folder for backups from project settings, or supply a default one.
    Can be adapted to project needs (for example using django-constance instead)
    """
    default_folder = os.path.join(settings.BASE_DIR, '..', 'dumps', 'localhost')
    folder = os.path.realpath(os.path.expanduser(
        getattr(settings, 'DUMP_LOCAL_DATA_TARGET_FOLDER', default_folder)
    ))
    return folder


def get_media_folder():
    return settings.MEDIA_ROOT


class Command(BaseCommand):
    help = 'Restore db and media from local backups; source folder is "{source_folder}"'.format(
        source_folder=get_source_folder()
    )

    def __init__(self, logger=None, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        signal.signal(signal.SIGINT, lambda signum, frame: sys.exit(0))

    def add_arguments(self, parser):
        parser.add_argument('prefix', help="Initial substring to match the filename to restore from; provide enough characters to match a single file")
        parser.add_argument('--target', '-t', metavar='target', choices=('db', 'media', 'all'), default='db', help="choices: db, media, all; default: db")
        parser.add_argument('--dry-run', '-d', action='store_true', dest='dry_run', default=False, help='Dry run (simulation)', )
        parser.add_argument('--no-gzip', action='store_false', dest='use_gzip', default=True, help='Do not compress result', )
        parser.add_argument('--source-subfolder', '-s', help='replaces "localhost" in DUMP_LOCAL_DATA_TARGET_FOLDER' )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.use_gzip = options['use_gzip']

        # prefix = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S_")
        prefix = options['prefix']
        db_name = settings.DATABASES['default']['NAME']

        source_folder = get_source_folder()
        source_subfolder = options['source_subfolder']
        if source_subfolder:
            # Replace "localhost" with given subfolder
            source_folder = os.path.join(
                os.path.split(source_folder)[0],
                source_subfolder,
            )

        if options['target'] in ['db', 'all']:
            self.restore_local_db(prefix, db_name, source_folder)

        if options['target'] in ['media', 'all']:
            self.restore_local_data(prefix, db_name, source_folder, get_media_folder())

    def run_command(self, command):
        """
        Execute specified system command;
        if running in dry-run mode; just display it
        """
        if self.dry_run:
            print("\x1b[1;37;40m# " + command + "\x1b[0m")
        else:
            print("\x1b[1;37;40m" + command + "\x1b[0m")
            rc = os.system(command)
            if rc != 0:
                raise Exception(command)

    def restore_local_db(self, prefix, db_name, source_folder):

        database = settings.DATABASES['default']
        assert 'postgresql' in settings.DATABASES['default']['ENGINE'], "This command applies only to Postgresql"

        filemask1 = '%s*_%s.sql' % (prefix, db_name)
        if self.use_gzip:
            filemask1 += '.gz'

        filemask2 = '%s*__postgresql.%s' % (prefix, db_name)
        if self.use_gzip:
            filemask2 += '.gz'

        files = glob.glob(os.path.join(source_folder, filemask1)) + glob.glob(os.path.join(source_folder, filemask2))

        if len(files) != 1:
            print('ERROR: unable to restore local db from file; nothing has been changed')
            print('Source folder: "%s"' % source_folder)
            print('Filemasks: "%s", "%s"' % (filemask1, filemask2))
            #print('List of matching files: %s' % str(files))
            print('List of matching files:')
            pprint(sorted(files))
        else:

            source_filename = files[0]

            name = database['NAME']
            user = database['USER']

            # Drop local tables
            self.run_command('psql --dbname="{name}" --command=\'drop owned by "{user}"\''.format(
                name=name,
                user=user
            ))

            command = 'gunzip -c ' if self.use_gzip else "cat "
            command += '"{source_filename}" | psql "{name}" --username "{user}"'.format(
                source_filename=source_filename,
                name=name,
                user=user,
            )
            self.run_command(command)

    def restore_local_data(self, prefix, db_name, source_folder, media_folder):

        filemask1 = '%s*_%s.media.tar' % (prefix, db_name)
        if self.use_gzip:
            filemask1 += '.gz'

        filemask2 = '%s*__home.%s.public.media' % (prefix, db_name)
        if self.use_gzip:
            filemask2 += '.tgz'
        else:
            filemask2 += '.tar'

        files = glob.glob(os.path.join(source_folder, filemask1)) + glob.glob(os.path.join(source_folder, filemask2))

        if len(files) != 1:
            print('ERROR: unable to restore local media from file; nothing has been changed')
            print('Source folder: "%s"' % source_folder)
            print('Filemasks: "%s", "%s"' % (filemask1, filemask2))
            #print('List of matching files: %s' % str(files))
            print('List of matching files:')
            pprint(sorted(files))
        else:
            source_filename = files[0]

            # Rebuild empty media folder
            command = "rm -fr %s" % media_folder
            self.run_command(command)
            command = "mkdir -p %s" % media_folder
            self.run_command(command)

            tar_options = "xvf"
            if self.use_gzip:
                tar_options = "z" + tar_options

            # The parent of "media"
            target_folder = os.path.dirname(media_folder)

            command = 'tar -C "{target_folder}" -{tar_options} "{source_filename}"'.format(
                target_folder=target_folder,
                tar_options=tar_options,
                source_filename=source_filename,
            )
            self.run_command(command)
