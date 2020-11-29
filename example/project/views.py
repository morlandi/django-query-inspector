from django.shortcuts import render
from django.utils import timezone
from backend.models import Track
from query_inspector import query_debugger
from query_inspector import qsdump
from query_inspector import trace_func
from query_inspector import prettyprint_queryset
from query_inspector.views import export_any_queryset
from query_inspector.views import export_any_dataset


@query_debugger
#@trace_func
def index(request):

    #tracks = Track.objects.all()
    tracks = Track.objects.select_related('album', 'album__artist', )[:10]

    #prettyprint_queryset(tracks, prettify=True, colorize=True)
    qsdump('*', queryset=tracks, max_rows=10)

    return render(request, 'index.html', {
        'tracks': tracks,
    })


def export_tracks_queryset(request, file_format='csv'):
    queryset = Track.objects.select_related('album', 'album__artist', )
    filename = '%s_%s.%s' % (
        timezone.localtime().strftime('%Y-%m-%d_%H-%M-%S'),
        "tracks",
        file_format,
    )

    return export_any_queryset(request, queryset, filename)


def export_tracks_dataset(request, file_format='csv'):
    queryset = Track.objects.select_related('album', 'album__artist', )
    filename = '%s_%s.%s' % (
        timezone.localtime().strftime('%Y-%m-%d_%H-%M-%S'),
        "tracks",
        file_format,
    )
    fields = [
        "id",
        "name|Track",
        "album|Album",
    ]

    return export_any_dataset(request, *fields, queryset=queryset, filename=filename)
