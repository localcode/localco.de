# localcode.views.py
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext



def home(request):
    c = {}
    return render_to_response(
            'home-index.html',
            c,
            )
