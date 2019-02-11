from django.urls import path

from ddbmeme.views import Search, autocompleteModel, maketextModel, makememeModel

urlpatterns = [
    path('', Search.as_view(), name='search_base'),
    path('load', autocompleteModel, name='autocompleteModel'),
    path('url', maketextModel, name='maketextModel'),
    path('meme', makememeModel, name='makememeModel'),
]
