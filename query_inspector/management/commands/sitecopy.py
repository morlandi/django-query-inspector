#import signal
import datetime
import time
import traceback
from django.core.management.base import BaseCommand
from django.conf import settings
from query_inspector.run_sitecopy import run_sitecopy

from query_inspector.app_settings import REMOTE_HOST
from query_inspector.app_settings import REMOTE_PROJECT_INSTANCE
from query_inspector.app_settings import REMOTE_MEDIA_FOLDER


def complain(*messages):
    print(' '.join(messages))


# def signal_handler(signal, frame):
#     sys.exit(0)


def sanity_checks():
    errors = 0

    project = REMOTE_PROJECT_INSTANCE
    if not project:
        complain(
            '"settings.SITECOPY_REMOTE_PROJECT_INSTANCE" is not defined; example:',
            'SITECOPY_REMOTE_PROJECT_INSTANCE = "%s"' % settings.DATABASES['default']['NAME']
        )
        errors += 1
        project = "[PROJECT]"

    remote_host = REMOTE_HOST
    if not remote_host:
        complain(
            '"settings.SITECOPY_REMOTE_HOST" is not defined;             example:',
            'SITECOPY_REMOTE_HOST = "%s.somewhere.net"' % project
        )
        errors += 1

    remote_media_folder = REMOTE_MEDIA_FOLDER
    if not remote_media_folder:
        complain(
            '"settings.SITECOPY_REMOTE_MEDIA_FOLDER" is not defined;     example:',
            'SITECOPY_REMOTE_MEDIA_FOLDER = "/home/%s/public/media/"' % project,
        )
        errors += 1

    if errors > 0:
        print("FATAL ERRORS ENCOUNTERED; UNABLE TO CONTINUE")
        exit(-1)


class Command(BaseCommand):

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     signal.signal(signal.SIGINT, signal_handler)

    # help = 'Syncs database and media files from remote project "{project}" running on remote server "{remote_server}"'.format(
    #     project=get_remote_project_instance(),
    #     remote_server=get_remote_host()
    # )
    help = 'Syncs database and media files from remote remote instance'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', '-d', action='store_true', dest='dry_run', default=False, help='Dry run (simulate actions)', )
        parser.add_argument('--quiet', '-q', action='store_true', default=False, help="do not require user confirmation before executing commands")

    def handle(self, *args, **options):

        sanity_checks()

        t0 = datetime.datetime.now()
        try:
            run_sitecopy(
                dry_run=options['dry_run'],
                interactive=not options['quiet'],
        )
        except Exception as e:
            print('ERROR: ' + str(e))
            print(traceback.format_exc())
        t1 = datetime.datetime.now()
        seconds = int((t1 - t0).total_seconds())
        print("Elapsed time: " + time.strftime("%H:%M:%S", time.gmtime(seconds)))
