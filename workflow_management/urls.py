from django.contrib import admin
from django.urls import path
from . import views


urlpatterns= [
    path('workflow/', views.workflow, name="workflow"),

    
]