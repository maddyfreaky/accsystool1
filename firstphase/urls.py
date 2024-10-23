from django.contrib import admin
from django.urls import path
from . import views
from .views import forgot_password, verify_otp, reset_password



urlpatterns= [
    path('members/',views.members,name="members"),
    # path('login/',views.member_login, name='login'),
    path('forms/',views.forms,name="forms"),
    path('table/', views.table, name="table"),
    path('register/', views.register_view, name="register"),
    path('', views.user_login, name="login"),
    path('logout/', views.user_logout, name='logout'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    path('reset-password/', reset_password, name='reset_password'),
    path('maintenance/', views.maintenance, name="maintenance")
    

    
]