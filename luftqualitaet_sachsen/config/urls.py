from django.conf.urls import include, patterns, url
from django.contrib import admin

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'luftqualitaet_sachsen.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', include('measuring_stations.urls'))
)
