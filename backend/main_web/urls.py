from django.contrib import admin
from django.urls import path,include
from django.views.generic import TemplateView
from .views import *

from django.views.generic import RedirectView

urlpatterns = [
    path('accounts/profile/', RedirectView.as_view(url='http://127.0.0.1:8000/home', permanent=True)),
    path('home',home),
    path('book',Book_view.as_view()),
    path('add-book',Book_post.as_view()),
    path('add',book_add_func),
]