from django.shortcuts import render
from backend.models import Track
from query_inspector import query_debugger


@query_debugger
def index(request):

    #tracks = Track.objects.all()
    tracks = Track.objects.select_related('album', 'album__artist', )

    return render(request, 'index.html', {
        'tracks': tracks[:1000],
    })
