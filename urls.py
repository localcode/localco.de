from django.conf.urls.defaults import patterns, include, url
import layers #, sites

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

    # sites
    (r'^sites/$', 'sites.views.index'),
    (r'^sites/create/$', 'sites.views.create'),
    (r'^sites/preview/$', 'sites.views.preview'),
    (r'^sites/build/$', 'sites.views.build'),
    (r'^sites/download/$', 'sites.views.download'),

    # admin
    (r'^admin/', include(admin.site.urls)),
    # admin documentation
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

)
