"""untitled1 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$','fred.views.betterboard'),
    url(r'^fred/$', 'fred.views.search'),
    url(r'^reset/&','fred.views.passwordreset',name='reset'),
    url(r'^friday/','kingfriday.views.index'),
    url(r'^leaderboard/','fred.views.betterboard',name='leaderboard'),
    url(r'^login/','django.contrib.auth.views.login'),
    url(r'^r/(?P<subname>.*)/$','fred.views.change_settings',name='change-settings'),
    url(r'^r/(?P<subname>.*)','fred.views.change_settings'),
    url(r'^logout/$','django.contrib.auth.views.logout',name='logout',kwargs={'next_page': '/'}),
    url(r'', include('django.contrib.flatpages.urls')),
]
