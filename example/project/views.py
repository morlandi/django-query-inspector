from django.shortcuts import render
from django.utils import timezone
from backend.models import Track
from query_inspector import query_debugger
from query_inspector import trace_func
from query_inspector import prettyprint_queryset
from query_inspector.views import export_any_queryset
from query_inspector.views import export_any_dataset
from query_inspector.templatetags.query_inspector_tags import render_queryset_as_table
from query_inspector.templatetags.query_inspector_tags import render_queryset_as_data
from query_inspector import qsdump, qsdump2


@query_debugger
#@trace_func
def index(request):

    #tracks = Track.objects.all()
    tracks = Track.objects.select_related('album', 'album__artist', )[:10]

    #prettyprint_queryset(tracks, prettify=True, colorize=True)
    qsdump2(queryset=tracks, exclude=['created', 'created_by', 'updated', 'updated_by', ], max_rows=10)
    qsdump2(queryset=[], exclude=['created', 'created_by', 'updated', 'updated_by', ], max_rows=10)

    fields = [
        "name|My Track",
        "id",
        "album|Album|enhanced",
        "album__id|Album id",
    ]

    html_table_tracks = render_queryset_as_table(
        *fields,
        queryset=tracks,
        options={
            'add_totals': True,
            'format_date': 'D d/m/Y',
        },
    )

    html_table_tracks_transposed = render_queryset_as_table(
        *fields,
        queryset=tracks,
        options={
            'add_totals': True,
            'format_date': 'D d/m/Y',
            'transpose': True,
        },
    )

    transposed = render_queryset_as_data(
        *["id", "name|Track", "album|Album", ],
        queryset=tracks,
        options={
            'transpose': True,
        },
    )

    return render(request, 'index.html', {
        'tracks': tracks,
        'html_table_tracks': html_table_tracks,
        'html_table_tracks_transposed': html_table_tracks_transposed,
        'transposed': transposed,
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
