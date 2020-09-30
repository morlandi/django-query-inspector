from django.shortcuts import render
from backend.models import Track
from query_inspector import query_debugger
from query_inspector import qsdump
from query_inspector import trace_func
from query_inspector import prettyprint_queryset


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
