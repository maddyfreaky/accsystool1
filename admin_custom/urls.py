from django.contrib import admin
from django.urls import path
from . import views


urlpatterns= [
    
    path('admin_custom/', views.admin_custom, name="admin_custom"),
    path('components/', views.components, name='components'),

]