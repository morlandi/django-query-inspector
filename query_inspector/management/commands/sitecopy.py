import signal
import datetime
import time
import traceback
import sys
import os
from django.core.management.base import BaseCommand
from django.conf import settings

try:
    # this raw_input is not converted by 2to3
    term_input = raw_input
except NameError:
    term_input = input

REMOTE_HOST_DEFAULT = getattr(settings, 'SITECOPY_REMOTE_HOST_DEFAULT', '<REMOTE_HOST>')
PROJECT = getattr(settings, 'SITECOPY_PROJECT', '<PROJECT>')
SOURCE_MEDIA_FOLDER = getattr(settings, 'SITECOPY_SOURCE_MEDIA_FOLDER', '/home/%s/public/media/' % PROJECT)

def signal_handler(signal, frame):
    sys.exit(0)

def prompt(message):
    print("\n\x1b[33m" + message + " \x1b[0m")

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = term_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")


class Command(BaseCommand):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        signal.signal(signal.SIGINT, signal_handler)

    help = 'Syncs database and media files for project "{project}" from remote server "{remote_server}"'.format(
        project=PROJECT,
        remote_server=REMOTE_HOST_DEFAULT
    )

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', '-d', action='store_true', dest='dry_run', default=False, help='Dry run (simulate actions)', )
        parser.add_argument('--quiet', '-q', action='store_true', default=False, help="do not require user confirmation before executing commands")
        parser.add_argument('--host', default=REMOTE_HOST_DEFAULT, help='Default: "{host}"'.format(host=REMOTE_HOST_DEFAULT))

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.quiet = options['quiet']
        self.host = options['host']
        t0 = datetime.datetime.now()

        # Sanity check
        errors = 0
        if REMOTE_HOST_DEFAULT == '<REMOTE_HOST>':
            print('ERROR: "SITECOPY_REMOTE_HOST_DEFAULT" setting is missing.')
            errors += 1
        if PROJECT == '<PROJECT>':
            print('ERROR: "SITECOPY_PROJECT" setting is missing.')
            errors += 1
        if errors > 0:
            return

        try:
            self.work()
        except Exception as e:
            print('ERROR: ' + str(e))
            print(traceback.format_exc())
        t1 = datetime.datetime.now()
        seconds = int((t1 - t0).total_seconds())
        print("Elapsed time: " + time.strftime("%H:%M:%S", time.gmtime(seconds)))

    def run_command(self, command):
        interactive = not self.quiet
        if self.dry_run:
            print("\x1b[1;37;40m# " + command + "\x1b[0m")
        else:
            print("\x1b[1;37;40m" + command + "\x1b[0m")

            if interactive and not query_yes_no("Proceed ?"):
                print('skipped')
            else:
                rc = os.system(command)
                if rc != 0:
                    raise Exception(command)

    def work(self):

        ########################################################################

        prompt("""(1) SYNC database "{project}" from remote server "{remote_server}":
Here, we assume that user "{project}" has access to database "{project}" on remote (source) server ...""".format(
    project=PROJECT,
    remote_server=self.host
))

        database = settings.DATABASES['default']
        name = database['NAME']
        user = database['USER']

        # Drop local tables
        assert 'postgresql' in settings.DATABASES['default']['ENGINE'], "This command applies only to Postgresql"
        self.run_command('psql --dbname="{name}" --command=\'drop owned by "{user}"\''.format(
            name=name,
            user=user
        ))

        # Dump remote db and feed local one
        # Example: ssh $PROJECT@www1.brainstorm.it "pg_dump --dbname=$PROJECT | gzip" | gunzip | psql $PROJECT
        command = 'ssh {dbname}@{remote_host} "pg_dump --no-owner --dbname={dbname} | gzip" | gunzip | psql "{name}" --username "{user}"'.format(
            remote_host=self.host,
            dbname=PROJECT,
            name=name,
            user=user
        )
        self.run_command(command)

        ########################################################################

        prompt("""(2) SYNC media for project "{project}" from remote server "{remote_server}":
Here we assume that user "{project}" can access remote server "{remote_server}" via SSH, having read access to source folder "{source_media_folder}" """.format(
    project=PROJECT,
    remote_server=self.host,
    source_media_folder=SOURCE_MEDIA_FOLDER,
))

        source = '{project}@{remote_host}:{source_media_folder}'.format(
            remote_host=self.host,
            project=PROJECT,
            source_media_folder=SOURCE_MEDIA_FOLDER,
        )
        target = settings.MEDIA_ROOT

        command = 'rsync -avz --progress --delete {source} {target}'.format(
            source=source,
            target=target,
        )
        self.run_command(command)
