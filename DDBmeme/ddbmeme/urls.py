import os

from django.urls import path
from django.views.generic import TemplateView

from ddbmeme.views import autocompletemodel, health, makemememodel, maketextmodel

path_prefix = os.environ.get('PATH_PREFIX', '').strip('/')
if path_prefix:
    path_prefix += '/'

urlpatterns = [
    path('healthz', health, name='health'),
    path(path_prefix, TemplateView.as_view(template_name='ddbmeme/search_form.html'), name='search_base'),
    path(path_prefix + 'load/', autocompletemodel, name='autocompletemodel'),
    path(path_prefix + 'url/', maketextmodel, name='maketextmodel'),
    path(path_prefix + 'meme/', makemememodel, name='makemememodel'),
]
