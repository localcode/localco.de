from localcode.views import *
from django.conf.urls.defaults import patterns, include, url
import webfinches #, islands

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    # home
    (r'^$', 'localcode.views.index'),
    #(r'^about/$', 'localcode.views.about'),
    #(r'^tools/$', 'localcode.views.tools'),

    # webfinches
    (r'^webfinches/$', 'webfinches.views.index'),
    (r'^webfinches/login/$', 'webfinches.views.login'),
    (r'^webfinches/login/create_account/$', 'webfinches.views.create_account'),
    (r'^webfinches/upload/$', 'webfinches.views.upload'),
    (r'^webfinches/review/$', 'webfinches.views.review'),
    (r'^webfinches/browse/configure/$', 'webfinches.views.configure'),
    (r'^webfinches/downloadtools/download/$', 'webfinches.views.download'),
    #(r'^webfinches/user/$', 'webfinches.views.user'),

		# Login / logout.
    #(r'^webfinches/login/$', 'django.contrib.auth.webfinches.views.login'),
    #(r'^webfinches/logout/$', logout_page),
    (r'^webfinches/', include('registration.backends.default.urls')),
    

    # Web portal.
    #(r'^portal/', include('portal.urls')),

    # Serve static content.
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': 'static'}),

    # webfinches api
    #(r'^webfinches/api/upload/$' 'webfinches.views.ajaxUpload'),
    #(r'^webfinches/api/info/$' 'webfinches.views.layerInfo'),

    # islands
    #(r'^islands/$', 'islands.views.index'),
    #(r'^islands/create/$', 'islands.views.create'),
    #(r'^islands/preview/$', 'islands.views.preview'),
    #(r'^islands/build/$', 'islands.views.build'),
    #(r'^islands/download/$', 'islands.views.download'),

    # admin
    (r'^admin/', include(admin.site.urls)),
    # admin documentation
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

)
