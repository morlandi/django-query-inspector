from django.shortcuts import render
from backend.models import Track
from query_inspector import query_debugger


@query_debugger
def index(request):

    tracks = Track.objects.all()[:100]

    return render(request, 'index.html', {
        'tracks': tracks,
    })
