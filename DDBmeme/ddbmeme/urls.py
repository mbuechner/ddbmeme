import os

from django.urls import path

from ddbmeme.views import Search, autocompletemodel, health, maketextmodel, makemememodel

path_prefix = os.environ.get('PATH_PREFIX', '')

urlpatterns = [
    path('healthz', health, name='health'),
    path(path_prefix, Search.as_view(), name='search_base'),
    path(path_prefix + 'load/', autocompletemodel, name='autocompletemodel'),
    path(path_prefix + 'url/', maketextmodel, name='maketextmodel'),
    path(path_prefix + 'meme/', makemememodel, name='makemememodel'),
]
