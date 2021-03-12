import os

from django.urls import path

from ddbmeme.views import Search, autocompletemodel, maketextmodel, makemememodel

urlpatterns = [
    path(os.environ.get('PATH_PREFIX', ''), Search.as_view(), name='search_base'),
    path(os.environ.get('PATH_PREFIX', '') + 'load/', autocompletemodel, name='autocompletemodel'),
    path(os.environ.get('PATH_PREFIX', '') + 'url/', maketextmodel, name='maketextmodel'),
    path(os.environ.get('PATH_PREFIX', '') + 'meme/', makemememodel, name='makemememodel'),
]
