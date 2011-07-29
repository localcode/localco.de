from django.conf.urls.defaults import patterns, include, url
import layers #, islands

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    # home
    (r'^$', 'localcode.views.index'),
    (r'^about/$', 'localcode.views.about'),
    (r'^tools/$', 'localcode.views.tools'),

    # layers
    (r'^layers/$', 'layers.views.index'),
    (r'^layers/upload/$', 'layers.views.upload'),
    (r'^layers/user/$', 'layers.views.user'),

    # islands
    (r'^islands/$', 'islands.views.index'),
    (r'^islands/create/$', 'islands.views.create'),
    (r'^islands/preview/$', 'islands.views.preview'),
    (r'^islands/build/$', 'islands.views.build'),
    (r'^islands/download/$', 'islands.views.download'),

    # admin
    (r'^admin/', include(admin.site.urls)),
    # admin documentation
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

)
