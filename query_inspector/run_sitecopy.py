import sys
import os
try:
    # this raw_input is not converted by 2to3
    term_input = raw_input
except NameError:
    term_input = input
from django.conf import settings


from .app_settings import REMOTE_HOST
from .app_settings import REMOTE_PROJECT_INSTANCE
from .app_settings import REMOTE_MEDIA_FOLDER
from .app_settings import PRE_CUSTOM_ACTIONS
from .app_settings import POST_CUSTOM_ACTIONS


def run_sitecopy(dry_run, interactive):

    assert REMOTE_HOST, "Missing setting SITECOPY_REMOTE_HOST"
    assert REMOTE_PROJECT_INSTANCE, "Missing setting SITECOPY_REMOTE_PROJECT_INSTANCE"
    assert REMOTE_MEDIA_FOLDER, "Missing setting SITECOPY_REMOTE_MEDIA_FOLDER"

    remote_host = REMOTE_HOST

    ########################################################################

    if PRE_CUSTOM_ACTIONS:
        prompt("""(0) Custom actions:""")
        for action in PRE_CUSTOM_ACTIONS:
            run_command(action, dry_run=dry_run, interactive=interactive)

    ########################################################################

    prompt("""(1) SYNC database "{project}" from remote server "{remote_server}":
Here, we assume that user "{project}" has access to database "{project}" on remote (source) server ...""".format(
project=REMOTE_PROJECT_INSTANCE,
remote_server=remote_host
))

    database = settings.DATABASES['default']
    name = database['NAME']
    user = database['USER']

    # Drop local tables
    assert 'postgresql' in settings.DATABASES['default']['ENGINE'], "This command applies only to Postgresql"
    command = 'psql --dbname="{name}" --command=\'drop owned by "{user}"\''.format(
        name=name,
        user=user
    )
    run_command(command, dry_run=dry_run, interactive=interactive)

    # Dump remote db and feed local one
    # Example: ssh $REMOTE_PROJECT_INSTANCE@www1.brainstorm.it "pg_dump --dbname=$REMOTE_PROJECT_INSTANCE | gzip" | gunzip | psql $REMOTE_PROJECT_INSTANCE
    command = 'ssh {dbname}@{remote_host} "pg_dump --no-owner --dbname={dbname} | gzip" | gunzip | psql "{name}" --username "{user}"'.format(
        remote_host=remote_host,
        dbname=REMOTE_PROJECT_INSTANCE,
        name=name,
        user=user
    )
    run_command(command, dry_run=dry_run, interactive=interactive)

    ########################################################################

    prompt("""(2) SYNC media for project "{project}" from remote server "{remote_server}":
Here we assume that user "{project}" can access remote server "{remote_server}" via SSH, having read access to source folder "{source_media_folder}" """.format(
project=REMOTE_PROJECT_INSTANCE,
remote_server=remote_host,
source_media_folder=REMOTE_MEDIA_FOLDER,
))

    source = '{project}@{remote_host}:{source_media_folder}'.format(
        remote_host=remote_host,
        project=REMOTE_PROJECT_INSTANCE,
        source_media_folder=REMOTE_MEDIA_FOLDER,
    )
    target = settings.MEDIA_ROOT

    command = 'rsync -avz --progress --delete {source} {target}'.format(
        source=source,
        target=target,
    )
    run_command(command, dry_run=dry_run, interactive=interactive)

    ########################################################################

    if POST_CUSTOM_ACTIONS:
        prompt("""(3) Custom actions:""")
        for action in POST_CUSTOM_ACTIONS:
            run_command(action, dry_run=dry_run, interactive=interactive)

#################################################################################
# helpers

def run_command(command, dry_run, interactive):
    if dry_run:
        print("\x1b[1;37;40m# " + command + "\x1b[0m")
    else:
        print("\x1b[1;37;40m" + command + "\x1b[0m")

        if interactive and not query_yes_no("Proceed ?"):
            print('skipped')
        else:
            rc = os.system(command)
            if rc != 0:
                raise Exception(command)


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
