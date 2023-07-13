import signal
import datetime
import time
import traceback
from django.core.management.base import BaseCommand
from django.conf import settings
from query_inspector.run_sitecopy import run_sitecopy

from query_inspector.app_settings import REMOTE_HOST
from query_inspector.app_settings import REMOTE_PROJECT_INSTANCE
from query_inspector.app_settings import REMOTE_MEDIA_FOLDER


def fail(*messages):
    print('FATAL ERROR:')
    print('\n'.join(messages))
    exit(-1)


def signal_handler(signal, frame):
    sys.exit(0)


def get_remote_project_instance():
    project = REMOTE_PROJECT_INSTANCE
    if not project:
        if getattr(settings, 'SITECOPY_PROJECT', ''):
            fail('DEPRECATION ERROR: setting "SITECOPY_PROJECT" has been replaced by "SITECOPY_REMOTE_PROJECT_INSTANCE"')
    if not project:
        fail(
            '"settings.SITECOPY_REMOTE_PROJECT_INSTANCE" is not defined; example:',
            'SITECOPY_REMOTE_PROJECT_INSTANCE = "%s"' % settings.DATABASES['default']['NAME']
        )
    return project


def get_remote_host():
    project = get_remote_project_instance()
    remote_host = REMOTE_HOST
    if not remote_host:
        if getattr(settings, 'SITECOPY_REMOTE_HOST_DEFAULT', ''):
            fail('DEPRECATION ERROR: setting "SITECOPY_REMOTE_HOST_DEFAULT" has been replaced by "SITECOPY_REMOTE_HOST"')
    if not remote_host:
        fail(
            '"settings.SITECOPY_REMOTE_HOST" is not defined; example:',
            'SITECOPY_REMOTE_HOST = "%s.somewhere.net"' % project
        )
    return remote_host


def get_remote_media_folder():
    project = get_remote_project_instance()
    remote_media_folder = REMOTE_MEDIA_FOLDER
    if not remote_media_folder:
        if getattr(settings, 'SITECOPY_SOURCE_MEDIA_FOLDER', ''):
            fail('DEPRECATION ERROR: setting "SITECOPY_SOURCE_MEDIA_FOLDER" has been replaced by "SITECOPY_REMOTE_MEDIA_FOLDER"')
    if not remote_media_folder:
        fail(
            '"settings.SITECOPY_REMOTE_MEDIA_FOLDER" is not defined; examples:',
            'SITECOPY_REMOTE_MEDIA_FOLDER = "/home/%s/public/media/" or:' % project,
            'SITECOPY_REMOTE_MEDIA_FOLDER = "/home/%s/data/media/" or:' % project,
        )
    return remote_media_folder



class Command(BaseCommand):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        signal.signal(signal.SIGINT, signal_handler)

    help = 'Syncs database and media files from remote project "{project}" running on remote server "{remote_server}"'.format(
        project=get_remote_project_instance(),
        remote_server=get_remote_host()
    )

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', '-d', action='store_true', dest='dry_run', default=False, help='Dry run (simulate actions)', )
        parser.add_argument('--quiet', '-q', action='store_true', default=False, help="do not require user confirmation before executing commands")

    def handle(self, *args, **options):

        # Sanity check
        get_remote_project_instance()
        get_remote_host()
        get_remote_media_folder()

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
