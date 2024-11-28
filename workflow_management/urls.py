from django.contrib import admin
from django.urls import path
from . import views
from .views import *


urlpatterns= [
    path('workflow/', views.workflow, name="workflow"),
    path('workflowmgt', views.workflowmgt, name='workflowmgt'),  
    # path('leavedetails', views.leavedetails, name='leavedetails'),  
    path('leave/', LeaveRequestView.as_view(), name='leave_request'),
    path('leave/<int:leave_id>/approve/', views.approve_leave, name='approve_leave'),
    path('leave/<int:leave_id>/reject/', views.reject_leave, name='reject_leave'), 
    path('withdraw_leave/<int:leave_id>/', WithdrawLeaveView.as_view(), name='withdraw_leave'),
 
    
]