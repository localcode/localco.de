# localcode.views.py
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext


def index(request):
    return render_to_response(
            'base.html',
            {},
            )
