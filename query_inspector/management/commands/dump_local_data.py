import os
import sys
import signal
import datetime
from django.conf import settings
from django.core.management.base import BaseCommand


def get_target_folder():
    """
    Retrieve target folder for backups from project settings, or supply a default one.
    Can be adapted to project needs (for example using django-constance instead)
    """
    default_folder = os.path.join(settings.BASE_DIR, '..', 'dumps', 'localhost')
    folder = os.path.realpath(os.path.expanduser(
        getattr(settings, 'DUMP_LOCAL_DATA_TARGET_FOLDER', default_folder)
    ))
    return folder


class Command(BaseCommand):
    help = 'Dump local db and media for backup purposes (and optionally remove old backup files)'

    def __init__(self, logger=None, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        signal.signal(signal.SIGINT, lambda signum, frame: sys.exit(0))

    def add_arguments(self, parser):
        parser.add_argument('--target', '-t', metavar='target', choices=('db', 'media', 'all'), default='db', help="choices: db, media, all; default: db")
        parser.add_argument('--dry-run', '-d', action='store_true', dest='dry_run', default=False, help='Dry run (simulation)', )
        parser.add_argument('--max-age', '-m', type=int, default=0, help='If > 0, remove backup files old "MAX_AGE days" or more')
        parser.add_argument('--no-gzip', action='store_false', dest='use_gzip', default=True, help='Do not compress result', )
        parser.add_argument('--legacy', action='store_true', default=False, help="use legacy Postgresql command syntax")

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.use_gzip = options['use_gzip']
        self.legacy = options['legacy']

        prefix = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S_")
        db_name = settings.DATABASES['default']['NAME']

        target_folder = get_target_folder()

        if options['target'] in ['db', 'all']:
            self.dump_local_db(prefix, db_name, target_folder)

        if options['target'] in ['media', 'all']:
            self.dump_local_data(prefix, db_name, target_folder)

        max_age = options['max_age']
        if max_age > 0:
            self.old_backups_cleanup(db_name, target_folder, max_age)

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

    def dump_local_db(self, prefix, db_name, target_folder):
        """
        Create a new db backup and save into backup folder
        """
        database = settings.DATABASES['default']
        assert 'postgresql' in settings.DATABASES['default']['ENGINE'], "This command applies only to Postgresql"

        filepath = os.path.join(target_folder, prefix + db_name + '.sql')
        if self.use_gzip:
            filepath += '.gz'

        # Prepare command to dump local db
        command = 'pg_dump {options}"{db_name}"'.format(
            options='--no-owner --dbname=' if not self.legacy else '',
            db_name=db_name
        )
        if self.use_gzip:
            command += " | gzip"
        command += ' > "%s"' % filepath

        self.run_command(command)

    def dump_local_data(self, prefix, db_name, target_folder):
        """
        Create a new media archive and save into backup folder
        """
        dump_filename = prefix + db_name + ".media.tar"
        dump_filepath = os.path.join(target_folder, dump_filename)

        # Prepare command to dump local media
        options = "cvf"
        if self.use_gzip:
            options = "z" + options
            dump_filepath += ".gz"
        # use MEDIA_ROOT parent as source folder
        source_folder = os.path.abspath(os.path.join(settings.MEDIA_ROOT, '..'))
        command = 'tar -C "%s" -%s "%s" "%s"' % (source_folder, options, dump_filepath, 'media')

        self.run_command(command)

    def old_backups_cleanup(self, db_name, target_folder, max_age):
        """
        Helper to remove backup files older than "max_age" days
        """

        # collect dated files from target folder
        files = []
        filter_pattern = '_' + db_name + '.'
        filenames = [name for name in os.listdir(target_folder) if filter_pattern in name]
        for filename in filenames:
            file_obj = DatedFile(filename)
            if file_obj.is_dated() and file_obj.age >= max_age:
                files.append(file_obj)

        # cleanup
        for file in files:
            print('Removing %s' % file)
            self.run_command('rm ' + os.path.join(target_folder, file.filename))


################################################################################
# Adapted form "easy_backup"

class DatedFile(object):
    """
    Helper to parse filename and, if dated (filename starts with "YYYY-MM-DD"),
    calculate it's age in days
    """

    filename = None
    filedate = None
    age = None

    def __init__(self, filename):
        self.filename = filename
        self.parse_filedate()
        if self.filedate is not None:
            self.age = (datetime.date.today() - self.filedate).days

    def parse_filedate(self):
        if self.filedate is None:
            # try "2018-03-22_..."
            try:
                self.filedate = datetime.datetime.strptime(self.filename[:10], "%Y-%m-%d").date()
            except:
                pass
        if self.filedate is None:
            # try "1521766816_2018_03_23_..."
            try:
                n = self.filename.find('_')
                self.filedate = datetime.datetime.strptime(self.filename[n+1:n+1+10], "%Y_%m_%d").date()
            except:
                pass

    def __str__(self):
        if self.filedate is None:
            return self.filename
        return '%s [dated:%s, age=%d]' % (
            self.filename,
            self.filedate,
            int(self.age),
        )

    def is_dated(self):
        return self.filedate is not None
