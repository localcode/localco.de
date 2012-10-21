from localcode.views import *
from django.conf.urls.defaults import patterns, include, url
import webfinches #, islands
from django.contrib import admin
from django.contrib.auth.views import login, logout
admin.autodiscover()


urlpatterns = patterns('',

    # home
    (r'^$', 'localcode.views.home'),
    #(home'^about/$', 'localcode.views.about'),
    #(r'^tools/$', 'localcode.views.tools'),

    # webfinches
    (r'^webfinches/$', 'webfinches.views.index'),
    #(r'^webfinches/login/create_account/$', 'webfinches.views.create_account'),
    (r'^webfinches/upload/$', 'webfinches.views.upload'),
    (r'^webfinches/review/$', 'webfinches.views.review'),
    (r'^webfinches/browse/$', 'webfinches.views.browse'),
    (r'^webfinches/configure/$', 'webfinches.views.configure'),
    (r'^webfinches/create_sites/$', 'webfinches.views.create_sites'),
    (r'^webfinches/get_sites/$', 'webfinches.views.get_sites'),
    #(r'^webfinches/user/$', 'webfinches.views.user'),

    # Login / logout.
    (r'^login/$', login, {'template_name': 'registration/login.html'}),
    (r'^logout/$', 'django.contrib.auth.views.logout' ),

    # Web portal.
    #(r'^portal/', include('portal.urls')),

    # Serve static content.
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': 'static'}),

    # webfinches api
    #(r'^webfinches/api/upload/$' 'webfinches.views.ajaxUpload'),
    #(r'^webfinches/api/info/$' 'webfinches.views.layerInfo'),

    # admin
    (r'^admin/', include(admin.site.urls)),
    # admin documentation
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

)
