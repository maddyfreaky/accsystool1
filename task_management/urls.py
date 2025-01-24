from django.urls import reverse
import re 
from django.utils.timesince import timesince
from django.http import JsonResponse
from django.utils.dateformat import format
from django.contrib import admin
from django.urls import path, include
from . import views


urlpatterns = [
    # path('task_management/',views.task_management,name='task_management'),
    path('todopgt/', views.todopgt, name='todopgt'),    
    path('projects/<int:project_id>/', views.projects, name='projects'),
    path('projects/<int:project_id>/create_issue/', views.create_issue, name='create_issue'),
    path('issue/edit/<int:issue_id>/', views.edit_issue, name='edit_issue'),

    path('issue/delete/<int:issue_id>/', views.delete_issue, name='delete_issue'),

    # path('register/', views.register, name='register'),  # URL for the register page
    # path('', views.user_login, name='login'),
    # path('logout/', views.user_logout, name='logout'),  # URL for the logout view
    path('projects/<int:project_id>/create-todolist/', views.create_todolist, name='create_todolist'),
    path('api/projects/all/', views.fetch_all_data, name='fetch_all_data'),
    path('todlistpage/', views.todlistpage, name='todlistpage'),
    path('project/delete/<int:project_id>/', views.delete_project, name='delete_project'),
    path('todotable/', views.todotable, name='todotable'),
    path('user_list/', views.user_list, name='user_list'),
    path('user-project/', views.user_project, name='user_project'),
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('user-project/create/', views.create_project, name='create_project'),
    path('update_status/<int:project_id>/', views.update_status, name='update_status'),
    path('assigned_projects_view/', views.assigned_projects_view, name='assigned_projects_view'),
    path('tasks/', views.task_view, name='task_view'),  # URL to render the tasks view
    path('update-task-status/<int:task_id>/', views.update_task_status, name='update_task_status'),
    path('project/edit/<int:project_id>/', views.edit_project, name='edit_project'),
    path('todo_card_detail_view/<int:task_id>/', views.todo_card_detail_view, name='todo_card_detail_view'),
    path('card_update_task_status/<int:task_id>/', views.card_update_task_status, name='card_update_task_status'),
    path('specific_user_tasks_view/<int:project_id>/', views.specific_user_tasks_view, name='specific_user_tasks_view'),
    path('specificprojectstask/<int:project_id>/users/<int:user_id>/tasks/add/', views.specific_user_task_view_task_mgt, name='specificusertask'),
    path('projects/<int:project_id>/tasks/', views.task_detail, name='task_detail'),  # Updated: No user_id
    path('create-task/<int:project_id>/', views.create_task, name='create_task'),  # Updated: No user_id
    path('todolist/create/<int:task_id>/', views.create_todolist, name='create_todolist'),
    path('delete_task/<int:task_id>/', views.delete_task, name='delete_task'),
    path('allprojects/', views.allprojects, name='allprojects'),
    path('all_projectss/', views.all_projectss, name='all_projectss'),
    path('task/update/<int:task_id>/', views.update_task, name='update_task'),
    path('all_projects_with_tasks/', views.all_projects_with_tasks, name='all_projects_with_tasks'),
    path('all_users_tasks/', views.all_users_tasks, name='all_users_tasks'),
    path('kanban-view/', views.get_tasks_for_kanban_view, name='kanban_view'),
    path('edit-task/', views.edit_task, name='edit_task'),
    path('add-comment/<int:task_id>/', views.add_comment, name='add_comment'),
    path('get-comments/<int:task_id>/', views.get_comments, name='get_comments'),
    path('mark-notifications-read/', views.mark_notifications_as_read, name='mark-notifications-read'),
    path('fetch-notifications/', views.fetch_notifications, name='fetch_notifications'),
    path('save-logout-time/', views.save_logout_time, name='save_logout_time'),
    path('loginusers/', views.loginusers, name='loginusers'),
    path('get-user-login-history/', views.get_user_login_history, name='get_user_login_history'),
    path('filter-login-history-by-date/', views.filter_login_history_by_date, name='filter_login_history_by_date'),  # new view for date filtering
    path('userprofile/', views.userprofile, name='userprofile'),
    path('profile/upload-image/', views.upload_profile_image, name='upload_profile_image'),
    path('profile/delete-image/', views.delete_profile_image, name='delete_profile_image'),
    path('meeting', views.meeting, name='meeting'),
    path('meetingsave/', views.meetingsave, name='meetingsave'),
    path('meeting_list', views.meeting_list,name='meeting_list'),
    path('meetingsend/<int:id>/', views.meetingsend, name='meetingsend'),
    path('after_meeting/<int:id>/', views.after_meeting, name='after_meeting'),
    path('delete_meeting/<int:id>/', views.delete_meeting, name='delete_meeting'),
    path('points_discussed/<int:id>/', views.points_discussed, name='points_discussed'),
    path('assign_tasks/<int:id>/', views.points_agreed, name='points_agreed'),
    path('minutes/<int:id>/', views.minutes_of_meeting, name='minutes_of_meeting'),
    path('send_mom/<int:id>/', views.send_mom, name='send_mom'),

    
]