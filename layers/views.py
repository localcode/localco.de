from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext


def index(request):
    """A view for browsing the existing layers.
    """
    return render_to_response(
            'layer-index.html',
            {},
            )

def upload(request):
    """A view for uploading new data.
    """
    return render_to_response(
            'layer-upload.html',
            {},
            )
