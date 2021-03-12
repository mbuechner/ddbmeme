from django.urls import path
from ddbmeme.views import Search, autocompleteModel, maketextModel, makememeModel
import os

urlpatterns = [
    path('test/', Search.as_view(), name='search_base'),
    path('test/load/', autocompleteModel, name='autocompleteModel'),
    path('test/url/', maketextModel, name='maketextModel'),
    path('test/meme/', makememeModel, name='makememeModel'),
]
