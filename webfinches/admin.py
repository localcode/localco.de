from django.contrib import admin

from webfinches.models import *



admin.site.register( UploadEvent )
admin.site.register( DataFile )
admin.site.register( DataLayer )
admin.site.register( Tag )
admin.site.register( SiteConfiguration )
admin.site.register( SiteSet )
admin.site.register( Site )

