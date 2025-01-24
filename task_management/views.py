from django.http import JsonResponse
from django.utils.dateformat import format
from django.utils import timezone
from .models import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.timesince import timesince
from django.views.decorators.http import require_POST
from django.urls import reverse
import re, pytz
from django.contrib import messages
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.db.models import Max
from django.utils.timezone import localtime, now
from django.contrib.auth.models import Group
from datetime import datetime, timedelta
from django.db.models import Sum
from django.utils.timezone import localtime
import os
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives





# Create your views here.

# def task_management(request):
#     return render(request,'task_management.html')
@login_required
def todlistpage(request):
    print("todolistpage function")

    if request.user.groups.filter(name="SuperAdmin").exists():
        # For SuperAdmin, fetch projects where the 'user' field is the logged-in user's ID
        projects = Project.objects.filter(user=request.user).distinct().order_by('-created_at')
        print("SuperAdmin projects:", projects)
    else:
        # For regular users, fetch projects that have tasks assigned to the logged-in user
        projects = Project.objects.filter(tasks__user=request.user).distinct().order_by('-created_at')
        print("Regular user projects:", projects)

    # Iterate through the projects and check the status of tasks
    for project in projects:
        # Check if all tasks for this project are completed
        if project.all_tasks_completed():
            print("Project all tasks completed")
            # Update the project status to 'Completed' if all tasks are completed
            if project.status != 'completed':
                project.status = 'completed'
                project.save()  # Save the updated status
        else:
            print("Project not all tasks completed")
            # Set project status to 'Pending Review' if not all tasks are completed
            if project.status != 'pending_review':
                project.status = 'pending_review'
                project.save()

    # Only show 'Pending' and 'Completed' as status choices for display purposes
    status_choices = [('pending_review', 'Pending'), ('completed', 'Completed')]
    print("Final project list:", projects)

    return render(request, 'todopage.html', {'projects': projects, 'status_choices': status_choices})

def todopgt(request):
     print("pgt function")
     if request.method == 'POST':
        projectname = request.POST.get('projectname')
        projectenddate = request.POST.get('projectdate')
        projectstatus = request.POST.get('projectpriority')
        if Project.objects.filter(projectname=projectname).exists():
            return JsonResponse({'status': 'error', 'message': 'Project name already exists.'})

        print(projectname)
        if projectname:
            print("pgt if")
            # Create and save the project
            Project.objects.create(
                projectname=projectname,
                to_date=projectenddate,
                priority=projectstatus,
                user=request.user,  # Assign the currently logged-in user
                assigned_by=request.user  # Assign the currently logged-in user as the creator

            )
            print("project saved")
            return redirect('todlistpage')  # Redirect to the project list page after saving
     return render(request,"todolist.html")

@login_required
def projects(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Retrieve all tasks related to the project and categorize them by status
    todo_tasks = project.details.filter(status='todo')
    in_progress_tasks = project.details.filter(status='in_progress')
    done_tasks = project.details.filter(status='done')

    # Combine project details and comments into one list (if needed for something else)
    combined_list = list(todo_tasks) + list(in_progress_tasks) + list(done_tasks)
    combined_list.sort(key=lambda x: x.created_at, reverse=True)

    # Calculate time ago for each task
    for item in combined_list:
        item.time_ago = timesince(item.created_at).split(', ')[-1]

    # Pass the categorized tasks to the template
    return render(request, 'todolist.html', {
        'project': project,
        'todo_tasks': todo_tasks,
        'in_progress_tasks': in_progress_tasks,
        'done_tasks': done_tasks,
    })


def create_issue(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        issuename = request.POST.get('issuename')
        print(issuename)
        if issuename:
            print("if",issuename)
            Issue.objects.create(project=project, title=issuename, description=issuename)
            return redirect('projects', project_id=project.id)
    
    return render(request, 'todolist.html', {'project': project})

def edit_issue(request, issue_id):
    issue = get_object_or_404(Issue, id=issue_id)
    
    if request.method == 'POST':
        issue.description = request.POST.get('description')
        issue.save()
        
        return redirect('projects', project_id=issue.project.id)  # Redirect to the project's issues view

    return render(request, 'edit_issue.html', {'issue': issue})

@require_POST
def delete_issue(request, issue_id):
    issue = get_object_or_404(Issue, id=issue_id)
    project_id = issue.project.id  # Capture the project ID before deleting
    issue.delete()
    return redirect('projects', project_id=project_id)  # Redirect to the projects view after deletion

@login_required
def create_todolist(request, task_id):
    task = get_object_or_404(Task, id=task_id)  # Get the task by its ID
    project = task.project  # Access the project via the task

    if request.method == 'POST':
        description = request.POST.get('description')
        comments = request.POST.get('comments')
        attached_files = request.FILES.getlist('attached_file[]')

        if description:
            todolist = Todolist(
                task=task,  # Associate to-do with a specific task
                project=project,
                description=description,
                comments=comments,
                status=task.status,  # Use the task's status
                user=request.user
            )
            todolist.save()

            for attached_file in attached_files:
                TodolistFile.objects.create(
                    todolist=todolist,
                    attached_file=attached_file
                )

            return redirect('todo_card_detail_view', task_id=task.id)

    return render(request, 'todolist.html', {'project': project})


def fetch_all_data(request):
    print("fetching all data")

    # Fetch all projects and tasks
    projects = Project.objects.all()
    todotasks = Todolist.objects.all()

    # Serialize project data
    data = []
    for project in projects:
        data.append({
            'id': project.id,
            'title': f"Project: {project.projectname}",  # Ensure projectname is the correct field
            'created_at': format(project.created_at, 'Y-m-dTH:i:sZ'),
        })

    # Serialize task data
    for task in todotasks:
        data.append({
            'id': task.id,
            'title': f"Comment for {task.project.projectname}",  # Use the correct field name
            'created_at': format(task.created_at, 'Y-m-dTH:i:sZ'),
            'description': task.description,  # Include the description field if needed
        })

    return JsonResponse(data, safe=False)

def todolist(request):
    print("todo")
    return render(request,"todolist.html")

def delete_project(request, project_id):
    print("Arun pgt function")
    project = get_object_or_404(Project, id=project_id)
    
    deleted_at_utc = timezone.now()  # Get the current time in UTC
    deleted_at_local = timezone.localtime(deleted_at_utc)


    archived_project = ArchivedProject(
        projectname=project.projectname,
        # taskname=project.taskname,
        priority=project.priority,
        from_date=project.from_date,
        to_date=project.to_date,
        created_at=project.created_at,
        updated_at=project.updated_at,
        deleted_at=deleted_at_local,  # Set the deletion date and time
  # Set the deletion date and time

        user=project.user,
        assigned_by=project.assigned_by,
        status=project.status,
    )
    archived_project.save()
    print(f"Project {project_id} deleted at {deleted_at_local.strftime('%Y-%m-%d %H:%M:%S')}")
    print("Deleted Projet Saved")

    # Delete the original project
    project.delete()
    
    return redirect('todlistpage')



@require_POST
def update_issue(request, issue_id):
    data = json.loads(request.body)
    try:
        issue = Issue.objects.get(pk=issue_id)
        issue.status = data['status']
        issue.updated_at = timezone.now()  # Update the timestamp
        issue.save()
        return JsonResponse({'success': True, 'message': 'Issue updated successfully'})
    except Issue.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Issue not found'}, status=404)


def todotable(request):
    project1 = Todolist.objects.all()
    print(project1,"this is test")
    return render(request,"todotable.html",{"project1":project1})

@login_required
def user_list(request):
    if request.user.groups.filter(name__in=["Admin", "SuperAdmin"]).exists():
        # Fetch all users excluding superusers (but include the logged-in Admin)
        superadmin_group = Group.objects.get(name='Superadmin')

# Exclude users who are in the "Superadmin" group
        users = User.objects.exclude(groups=superadmin_group)        
        return render(request, 'user_list.html', {'users': users})
    else:
        # Redirect non-superusers or show a permission denied message
        return JsonResponse({'error': 'Permission Denied'}, status=403)


def user_project(request):
    print("user_project function")

    # Get all projects excluding SuperAdmin-related projects
    user_projects = Project.objects.exclude(user__groups__name='SuperAdmin').order_by('-created_at')
    print("Filtered user_projects (excluding SuperAdmin projects):", user_projects)

    context = {
        'projects': user_projects,  # Pass all filtered projects
    }

    return render(request, 'user_project.html', context)




def create_project(request):
    print("create_project function")

    if request.method == 'POST':
        # Get form data from POST request
        projectname = request.POST.get('projectname')
        taskname = request.POST.get('taskname')
        priority = request.POST.get('priority')
        from_date = request.POST.get('fromdate')
        to_date = request.POST.get('todate')
        # default_user = get_object_or_404(User, username='Punithan')

        if Project.objects.filter(projectname=projectname).exists():
            return JsonResponse({'status': 'error', 'message': 'Project name already exists, please give a different name'})

        try:
            print("try block")
            # Create and save new Project instance
            project = Project(
                projectname=projectname,
                priority=priority,
                from_date=from_date,
                to_date=to_date,
                assigned_by=request.user,  # Set the user creating the project
                user=None, 
            )
            project.save()
            print("Project data saved")

            # Redirect back to the user's project page
            return redirect('user_project')

        except Exception as e:
            print("except")
            return HttpResponse(f"An error occurred: {e}", status=500)

    return render(request, 'create_project.html')

@require_POST
def update_status(request, project_id):
    status_value = request.POST.get('status')
    project = get_object_or_404(Project, id=project_id)
    if status_value in dict(Project.STATUS_CHOICES).keys():  # Validate status
        project.status = status_value
        project.save()
    return redirect('todlistpage') # Redirect to the project list page after saving as needed

@login_required
def assigned_projects_view(request):
    if request.user.is_authenticated:
        # Fetch projects assigned to the currently logged-in user
        projects = Project.objects.filter(user=request.user)
        print(projects,"username")
    else:
        projects = Project.objects.none()  # No projects if not authenticated
        print(projects,"username else")


    context = {
        'projects': projects
    }
    return render(request, 'todopage.html', context)

def task_view(request):
    todotasks = Todolist.objects.filter(status='todo')
    in_progress_tasks = Todolist.objects.filter(status='in_progress')
    done = Todolist.objects.filter(status='done')

    context = {
        'todotask': todotasks,
        'in_progress_tasks': in_progress_tasks,
    }

    return render(request, 'todolist.html', context)

@csrf_exempt
def update_task_status(request, task_id):
    if request.method == 'POST':
        try:
            # Parse the request body to get the new status
            data = json.loads(request.body)
            new_status = data.get('status')

            # Fetch the task using the Task model
            task = Task.objects.get(id=task_id)

            # Ensure the new status is different before updating
            if task.status != new_status:
                # Update the task's status and status_updated_at
                task.status = new_status
                task.status_updated_at = now()
                task.save()

                # Identify the current user (the one performing the action)
                current_user = request.user

                # Notify the assigned user, if not the current user
                if task.user != current_user:
                    Notification.objects.create(
                        user=task.user,
                        message=f"Your task '{task.taskname}' status was changed to {new_status} by '{current_user}'.",
                        assigned_by=current_user
                    )

                # Notify the assigner, if not the current user and not the assigned user
                if task.assigned_by and task.assigned_by != current_user and task.assigned_by != task.user:
                    Notification.objects.create(
                        user=task.assigned_by,
                        message=f"The task '{task.taskname}' assigned to {task.user.username} was updated to {new_status}.",
                        assigned_by=current_user
                    )

            # Return a success response
            return JsonResponse({'success': True})

        except Task.DoesNotExist:
            return JsonResponse({'error': 'Task not found'}, status=404)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    # Return an error response if the request method is not POST
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        project.projectname = request.POST.get('projectname')
        project.taskname = request.POST.get('taskname')
        project.priority = request.POST.get('priority')
        project.from_date = request.POST.get('fromdate')
        project.to_date = request.POST.get('todate')
        
        project.save()
        return redirect('todlistpage')
    
    return HttpResponse("Invalid request method.", status=400)

def todo_card_detail_view(request, task_id):
    task = get_object_or_404(Task, id=task_id)  # Get the task by ID
    todolist_entries = Todolist.objects.filter(task=task)  # Filter to-dos by task

    task_counts = {
        'todo': todolist_entries.filter(status='todo').count(),
        'in_progress': todolist_entries.filter(status='in_progress').count(),
        'done': todolist_entries.filter(status='done').count(),
    }

    context = {
        'task': task,
        'task_counts': task_counts,
        'todolist_entries': todolist_entries  # Filtered to-dos for this task
    }

    return render(request, 'usercard.html', context)

from django.shortcuts import redirect, render, get_object_or_404
from .models import Task, Project  # Adjust the import based on your app structure

def card_update_task_status(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if request.method == 'POST':
        status = request.POST.get('status')

        # Ensure the provided status is valid
        if status in dict(Task.STATUS_CHOICES).keys() and task.status != status:
            # Update task status and timestamp
            task.status = status
            task.status_updated_at = now()
            task.save()

            # Identify the current user (the one performing the action)
            current_user = request.user

            # Notify the assigned user, if not the current user
            if task.user != current_user:
                Notification.objects.create(
                    user=task.user,
                    message=f"Your task '{task.taskname}' status was changed to {status} by '{current_user}'.",
                    assigned_by=current_user
                )

            # Notify the assigner, if not the current user and not the assigned user
            if task.assigned_by and task.assigned_by != current_user and task.assigned_by != task.user:
                Notification.objects.create(
                    user=task.assigned_by,
                    message=f"The task '{task.taskname}' assigned to {task.user.username} was updated to {status}.",
                    assigned_by=current_user
                )

    # Redirect to the same page (current page)
    return redirect(request.META.get('HTTP_REFERER', 'all_projects_with_tasks'))
    
def specific_user_tasks_view(request, project_id):
    # Retrieve the project based on the project ID
    project = Project.objects.get(id=project_id)

    # Retrieve tasks for this project that are assigned to the logged-in user
    tasks = Task.objects.filter(project=project, user=request.user)

    # Add a property to child tasks indicating whether the parent task is completed
    processed_tasks = []
    for task in tasks:
        if task.is_child:
            if task.parent_task.status != 'Completed':
                task.is_faded = True  # Mark as faded
            else:
                task.is_faded = False  # No fade if parent is completed
        else:
            task.is_faded = False  # Regular tasks are not faded
        processed_tasks.append(task)

    context = {
        'project': project,
        'tasks': processed_tasks
    }

    return render(request, 'specific_user_task.html', context)

def specific_user_task_view_task_mgt(request, project_id, user_id):
    if request.method == 'POST':
        # Retrieve project and user objects
        project = get_object_or_404(Project, id=project_id)
        user = get_object_or_404(User, id=user_id)

        # Get form data
        taskname = request.POST.get('taskname')
        priority = request.POST.get('priority')
        from_date = request.POST.get('fromdate')
        to_date = request.POST.get('todate')
        description= request.POST.get('description')

        # Create a new task object
        task = Task(
            taskname=taskname,
            priority=priority,
            from_date=from_date,
            to_date=to_date,
            description=description,
            user=user,
            project=project
        )
        task.save()

        # Display success message and redirect to project page (or wherever you want)
        # messages.success(request, 'Task created successfully.')
        return redirect('specific_user_tasks_view', project_id=project.id)

    else:
        # If it's a GET request, render the form page
        return render(request, 'specific_user_task_form.html')

def task_detail(request, project_id):
    project = Project.objects.get(id=project_id)
    tasks = Task.objects.filter(project=project)  # Fetch all tasks for the project

    # Fetch all tasks related to this project for parent task dropdown
    all_tasks = Task.objects.filter(project=project)
    superadmin_group = Group.objects.get(name='Superadmin')
    excluded_users = User.objects.filter(groups=superadmin_group)
    available_users = User.objects.exclude(id__in=excluded_users.values_list('id', flat=True))

    return render(request, 'task_detail.html', {
        'tasks': tasks,
        'selected_project': project,
        'all_tasks': all_tasks,  # Passing all tasks for parent task selection
        'available_users': available_users
    })



from django.contrib.auth.models import User

from django.core.mail import send_mail
from django.conf import settings

from django.core.exceptions import ValidationError
from django.contrib import messages

def create_task(request, project_id):
    if request.method == 'POST':
        project = get_object_or_404(Project, id=project_id)

        # Get task details from the POST request
        taskname = request.POST.get('taskname')
        priority = request.POST.get('priority')
        from_date = request.POST.get('fromdate')
        to_date = request.POST.get('todate')
        description = request.POST.get('description')
        is_child = request.POST.get('is_child') == 'on'
        parent_task_id = request.POST.get('parent_task')

        if is_child and not parent_task_id:
            messages.error(request, "Please select a parent task when 'Is Child' is checked.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        # Get selected users from the POST request
        selected_user_ids = request.POST.getlist('selected_users')
        selected_users = User.objects.filter(id__in=selected_user_ids)

        if not selected_users:
            # Handle case where no users are selected
            messages.error(request, "Please select at least one user to assign the task.")
            return redirect('create_task', project_id=project_id)

        # Create tasks for each selected user
        for user in selected_users:
            task = Task.objects.create(
                taskname=taskname,
                priority=priority,
                from_date=from_date,
                to_date=to_date,
                project=project,
                user=user,
                description=description,
                is_child=is_child,
                assigned_by=request.user
            )

            # Link parent task if "Is Child" is checked
            if is_child and parent_task_id:
                parent_task = Task.objects.get(id=parent_task_id)
                task.parent_task = parent_task
                task.save()

            # Create notification for each user
            Notification.objects.create(
                user=user,
                message=f"Task '{taskname}' created by {request.user.username}",
                assigned_by=request.user
            )

            # Send email notification to the user
            if user.email:  # Ensure the user has an email address
                subject = f"New Task Assigned: {taskname}"
                message = (
                    f"Dear {user.username},\n\n"
                    f"A new task has been assigned to you in the project '{project.projectname}'.\n"
                    f"Details:\n"
                    f"Task Name: {taskname}\n"
                    f"Priority: {priority}\n"
                    f"From Date: {from_date}\n"
                    f"To Date: {to_date}\n"
                    f"Description: {description}\n\n"
                    f"Please log in to the system to view more details.\n\n"
                    f"Best regards,\n"
                    f"{request.user.username}\n\n"
                    f"This is a system-generated email, please do not reply."
                )
                try:
                    send_mail(
                        subject,
                        message,
                        settings.EMAIL_HOST_USER,  # The sender's email address
                        [user.email],  # List of recipient email addresses
                        fail_silently=False,
                    )
                except Exception as e:
                    # Handle email sending errors
                    print(f"Failed to send email to {user.email}: {e}")

        # Redirect to the task details page
        return redirect('task_detail', project_id=project.id)

    
def mark_notifications_as_read(request):
    user = request.user
    if request.method == 'POST':  # Ensure it's a POST request
        # Mark all unread notifications for this user as read
        Notification.objects.filter(user=user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)  # Return an error for non-POST requests




def fetch_notifications(request):
    user = request.user  # Get the logged-in user
    notifications = Notification.objects.filter(user=user).order_by('-created_at')  # Fetch user's notifications
    kolkata_tz = pytz.timezone('Asia/Kolkata')  # Define Kolkata timezone

    notification_data = [{
        'assigned_by': notification.assigned_by.username,  # Show the username of the person who assigned the task
        'task_name': notification.message.split(" created the task ")[-1],  # Extract just the task name
        'created_at': notification.created_at.astimezone(kolkata_tz).strftime('%Y-%m-%d %I:%M %p')  # Format time in Kolkata timezone
    } for notification in notifications]

    # Fetch unread notifications for count
    unread_count = Notification.objects.filter(user=user, is_read=False).count()

    return JsonResponse({'notifications': notification_data, 'unread_count': unread_count})

@login_required
def delete_task(request, task_id):
    
    if request.method == 'POST':  # Only allow POST request for deletion
        try:
            # Get the task to delete
            task = get_object_or_404(Task, id=task_id)
            deleted_at = localtime()

            # Backup the task details before deleting
            DeletedTask.objects.create(
                taskname=task.taskname,
                priority=task.priority,
                from_date=task.from_date,
                to_date=task.to_date,
                user=task.user,
                project=task.project,
                deleted_at=deleted_at
            )

            # Delete the task from the Task table
            task.delete()

            # Return success response
            return JsonResponse({
                'status': 'success',
                'message': 'Task deleted successfully!',
                'deleted_at': deleted_at.strftime("%d-%m-%Y %H:%M:%S")
            }, status=200)

        except Exception as e:
            # Return error response if something goes wrong
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    # If the request method is not POST, return a bad request
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)


def allprojects(req):
    print("hello")
    # Get the current user's groups
    user_groups = req.user.groups.values_list('name', flat=True)

    # Exclude projects for 'superadmin' and 'normaluser' groups
    if 'superadmin' in user_groups:
        print("all")
        # Show all projects or projects specific to superadmin
        projects = Project.objects.all()  # Adjust based on your logic
    elif 'normaluser' in user_groups:
        # Exclude normal user projects (you can adjust the filter based on the logic you need)
        projects = Project.objects.exclude(user_groups_name='normaluser')
    else:
        # If the user belongs to any other group, fetch all their assigned projects
        projects = Project.objects.filter(user=req.user)

    return render(req, "allprojects.html", {'projects': projects})

from django.shortcuts import render
from django.contrib.auth.models import Group
from .models import Project

def all_projectss(request):
    # Get the Superadmin group
    superadmin_group = Group.objects.get(name='Superadmin')

    # Exclude projects where the user belongs to the Superadmin group
    projects = Project.objects.exclude(user__groups=superadmin_group).order_by('-created_at')

    context = {
        'projects': projects
    }
    return render(request, 'all_projects1.html', context)

def update_task(request, task_id):
    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id)
        task.taskname = request.POST.get('taskname')
        task.description = request.POST.get('description')  # Update description
        task.priority = request.POST.get('priority')
        task.from_date = request.POST.get('fromdate')
        task.to_date = request.POST.get('todate')
        task.save()

        return JsonResponse({'status': 'success'})  # Return success response

    return JsonResponse({'status': 'error'}, status=400)  # Handle GET requests or invalid methods

    return redirect('task_detail', project_id=task.project.id)  # Fallback redirect

def all_projects_with_tasks(request):
    print("Fetching tasks for the user")

    if request.user.is_authenticated:
        # Fetch all projects (common to all users)
        projects = Project.objects.all().order_by('-created_at')

        user_tasks = []  # To store tasks assigned to the logged-in user
        selected_status = request.POST.get('status') if request.method == 'POST' else None

        # Iterate over each project to get tasks specific to the logged-in user
        for project in projects:
            # Filter tasks for the logged-in user
            tasks = project.tasks.filter(user=request.user)
            if selected_status:  # Apply status filter if provided
                tasks = tasks.filter(status=selected_status)

            # Filter out child tasks if their parent is not completed
            filtered_tasks = []
            for task in tasks:
                if not task.is_child:  # If the task is not a child, add it
                    filtered_tasks.append({
                        'task': task,
                        'disabled': False  # Not disabled
                    })
                elif task.is_child:
                    # If the parent task is not completed, mark it as disabled
                    disabled = task.parent_task.status != 'Completed'
                    filtered_tasks.append({
                        'task': task,
                        'disabled': disabled  # Mark child task as disabled based on parent's status
                    })

            if filtered_tasks:  # Add only if there are tasks to display after filtering
                user_tasks.append({
                    'project': project,
                    'tasks': filtered_tasks
                })
            print(f"Tasks for {project.projectname} assigned to {request.user.username}: {filtered_tasks}")

        # Pass the user's tasks and projects to the template
        context = {
            'user_tasks': user_tasks,  # This will hold projects with tasks specific to the user
            'selected_status': selected_status, 
        }
        print("Rendering HTML with user-specific tasks")
        return render(request, 'all_projects_with_tasks.html', context)

    else:
        # Redirect to login page if not authenticated
        return redirect('login')


    
from django.contrib.auth.models import Group

def all_users_tasks(request):
    if request.user.is_authenticated:
        # Check if the user is either a Superadmin or Admin
        if request.user.groups.filter(name__in=['Superadmin', 'Admin']).exists():
            # Fetch projects excluding the current user's own projects
            projects = Project.objects.exclude(user=request.user).order_by('-created_at')

            # Check if the logged-in user is an Admin (but not a Superadmin)
            if request.user.groups.filter(name='Admin').exists():
                # Fetch tasks excluding those related to Superadmin users
                superadmin_group = Group.objects.get(name='Superadmin')
                superadmin_users = superadmin_group.user_set.all()

                # Exclude tasks from projects created by Superadmin users
                tasks = Task.objects.filter(project__in=projects).exclude(project__user__in=superadmin_users).order_by('-from_date')
            else:
                # If the logged-in user is a Superadmin, show all tasks
                tasks = Task.objects.filter(project__in=projects).order_by('-from_date')
             # Apply status filter if selected
            selected_status = request.POST.get('status', None)
            if selected_status:
                tasks = tasks.filter(status=selected_status)
            
            context = {
                'projects': projects,
                'tasks': tasks,  # Pass the filtered tasks to the template
                'selected_status': selected_status,
            }

            return render(request, 'allusertasks.html', context)
        else:
            return render(request, 'unauthorized.html')  
    else:
        return redirect('login')


def kanban_view(request):
    if request.user.is_authenticated:
        # Fetch tasks for the logged-in user
        tasks = Task.objects.filter(project__user=request.user).order_by('-from_date')

        context = {
            'tasks': tasks,  # Pass the tasks to the template
        }
        return render(request, 'usercard.html', context)
    else:
        return redirect('login')
    
def edit_task(request):
    if request.method == 'POST':
        task_id = request.POST.get('task_id')
        task_name = request.POST.get('taskname')
        task_status = request.POST.get('status')

        # Get the task object and update it with the new data
        task = get_object_or_404(Task, id=task_id)
        task.taskname = task_name
        task.status = task_status
        task.save()

        return redirect('kanban_view')  # Redirect to the Kanban view after updating

    return redirect('kanban_view')

@login_required
def get_tasks_for_kanban_view(request):
    user = request.user
    
    # Filter tasks based on the logged-in user and their statuses
    todo_tasks = Task.objects.filter(user=user, status='Not Started')
    in_progress_tasks = Task.objects.filter(user=user, status='Working')
    completed_tasks = Task.objects.filter(user=user, status='Completed')
    pending_review_tasks = Task.objects.filter(user=user, status='Pending Review')
    cancelled_tasks = Task.objects.filter(user=user, status='Cancelled')
    rework_tasks = Task.objects.filter(user=user, status='Rework')  # New line for Rework tasks

    # Filtering child tasks based on parent status
    def filter_child_tasks(tasks):
        filtered_tasks = []
        for task in tasks:
            if not task.is_child:
                filtered_tasks.append(task)
            elif task.is_child and task.parent_task.status == 'Completed':
                filtered_tasks.append(task)
        return filtered_tasks

    todo_tasks_custom = filter_child_tasks(todo_tasks)
    in_progress_tasks_custom = filter_child_tasks(in_progress_tasks)
    completed_tasks_custom = filter_child_tasks(completed_tasks)
    pending_review_tasks_custom = filter_child_tasks(pending_review_tasks)
    cancelled_tasks_custom = filter_child_tasks(cancelled_tasks)
    rework_tasks_custom = filter_child_tasks(rework_tasks)  # Filtering Rework tasks

    context = {
        'todo_tasks_custom': todo_tasks_custom,
        'in_progress_tasks_custom': in_progress_tasks_custom,
        'completed_tasks_custom': completed_tasks_custom,
        'pending_review_tasks_custom': pending_review_tasks_custom,
        'cancelled_tasks_custom': cancelled_tasks_custom,
        'rework_tasks_custom': rework_tasks_custom,  # Adding to context
    }
    
    return render(request, 'usercard.html', context)

@csrf_exempt
def get_comments(request, task_id):
    comments = Comment.objects.filter(task_id=task_id).values('text', 'comment_timestamp', 'user__username')

    comments_list = [
        {
            'text': comment['text'],
            'timestamp': timezone.localtime(comment['comment_timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
            'username': comment['user__username']  # Include the username
        }
        for comment in comments
    ]

    return JsonResponse({'success': True, 'comments': comments_list})

@csrf_exempt
def add_comment(request, task_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        comment_text = data.get('comment')

        task = Task.objects.get(id=task_id)

        # Get the logged-in user
        user = request.user

        # Create the new comment and associate it with the user
        new_comment = Comment.objects.create(task=task, text=comment_text, user=user)

        return JsonResponse({
            'success': True,
            'comment': new_comment.text, 
            'timestamp': new_comment.comment_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'username': new_comment.user.username  # Return username
        })
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def delete_user(request, user_id):
    if request.user.is_superuser:
        user = get_object_or_404(User, id=user_id)
        
        # Archive the user details before deletion
        ArchivedUser.objects.create(
            username=user.username,
            email=user.email,
            date_joined=user.date_joined
        )
        
        # Delete the user
        user.delete()
        
        return JsonResponse({'success': 'User deleted successfully.'})
    else:
        return JsonResponse({'error': 'Permission Denied'}, status=403)

@csrf_exempt
def save_logout_time(request):
    print("logout time")
    if request.method == "POST" and request.user.is_authenticated:
        try:
            # Get the last login history record for the current user
            last_login_record = LoginHistory.objects.filter(user=request.user).last()
            if last_login_record and not last_login_record.logout_time:
                # Update the logout time
                kolkata_timezone = pytz.timezone('Asia/Kolkata')  # Set to IST
                logout_time_utc = timezone.now()  # Current time in UTC
                logout_time_local = logout_time_utc.astimezone(kolkata_timezone)  # Convert to IST
                
                last_login_record.logout_time = logout_time_utc  # Save in UTC
                last_login_record.save()
                
                # Debug logs for UTC and local time
                print(f"Logout time (UTC): {logout_time_utc}")
                print(f"Logout time (Local): {logout_time_local}")
                print("logout time saved")
                
                return JsonResponse({"success": True, "message": "Logout time saved successfully."})
            return JsonResponse({"success": False, "message": "No active session found."})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})
    return JsonResponse({"success": False, "message": "Invalid request."})

@csrf_exempt
def filter_login_history_by_date(request):
    print("Function called")  # Debugging log
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        selected_date = request.POST.get("selected_date")

        print(f"Received user_id: {user_id}, selected_date: {selected_date}")  # Debugging log

        if user_id and selected_date:
            # Get the selected date in Kolkata timezone
            kolkata_timezone = pytz.timezone('Asia/Kolkata')
            selected_date = timezone.datetime.strptime(selected_date, '%Y-%m-%d').date()

            # Define the start and end of the selected date
            start_of_day = timezone.datetime.combine(selected_date, timezone.datetime.min.time(), tzinfo=kolkata_timezone)
            end_of_day = timezone.datetime.combine(selected_date, timezone.datetime.max.time(), tzinfo=kolkata_timezone)

            # Filter login history by user_id and the selected date range (from start of the day to the end of the day)
            login_history = LoginHistory.objects.filter(
                user_id=user_id,
                login_time__range=(start_of_day, end_of_day)  # Filter by selected date range
            ).order_by('-login_time')

            # Calculate total time spent today
            total_time_spent = timedelta()

            data = []
            for entry in login_history:
                login_time = entry.login_time.astimezone(kolkata_timezone)
                logout_time = entry.logout_time.astimezone(kolkata_timezone) if entry.logout_time else None

                # Calculate time spent for this session
                if logout_time:
                    time_spent = logout_time - login_time
                else:
                    time_spent = timezone.now() - login_time  # Time spent until now if still logged in

                total_time_spent += time_spent

                data.append({
                    "login_time": login_time.strftime("%d-%m-%Y %H:%M:%S"),
                    "logout_time": (logout_time.strftime("%d-%m-%Y %H:%M:%S") 
                                    if logout_time else "Currently logged in"),
                    "time_spent": str(time_spent).split(".")[0]  # Show in HH:MM:SS format
                })

            # Format total time spent in HH:MM:SS
            total_hours, remainder = divmod(total_time_spent.seconds, 3600)
            total_minutes, total_seconds = divmod(remainder, 60)
            total_time_formatted = f"{total_hours:02}:{total_minutes:02}:{total_seconds:02}"

            print(f"Login history data: {data}")  # Debugging log
            return JsonResponse({"success": True, "data": data, "total_time": total_time_formatted})
        
        return JsonResponse({"success": False, "error": "User ID or Date not provided"})
    
    return JsonResponse({"success": False, "error": "Invalid request"})

def loginusers(request):
    # Fetch all users
    users = User.objects.all()
    return render(request, "loginusers.html", {"users": users})



@csrf_exempt  # Remove this in production if CSRF tokens are properly included
def get_user_login_history(request):
    print("Function called")  # Debugging log
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        print(f"Received user_id: {user_id}")  # Debugging log
        if user_id:
            # Get today's date in Kolkata timezone
            kolkata_timezone = pytz.timezone('Asia/Kolkata')
            today = timezone.now().astimezone(kolkata_timezone).date()

            # Define the start and end of today's date
            start_of_day = timezone.datetime.combine(today, timezone.datetime.min.time(), tzinfo=kolkata_timezone)
            end_of_day = timezone.datetime.combine(today, timezone.datetime.max.time(), tzinfo=kolkata_timezone)

            # Filter login history by user_id and today's date range (from start of the day to the end of the day)
            login_history = LoginHistory.objects.filter(
                user_id=user_id,
                login_time__range=(start_of_day, end_of_day)  # Filter by today's date range
            ).order_by('-login_time')
            print(f"Login history for today: {login_history}")  # Debugging log
            
            total_time = 0  # Initialize total time in seconds

            # Prepare data with formatted login and logout times in Kolkata timezone
            data = []
            for entry in login_history:
                login_time = entry.login_time.astimezone(kolkata_timezone)
                logout_time = entry.logout_time.astimezone(kolkata_timezone) if entry.logout_time else None

                # Calculate session duration in seconds
                if logout_time:
                    session_duration = (logout_time - login_time).total_seconds()
                    total_time += session_duration
                    logout_time_str = logout_time.strftime("%d-%m-%Y %H:%M:%S")
                else:
                    session_duration = 0
                    logout_time_str = "Currently logged in"

                # Add entry data
                data.append({
                    "login_time": login_time.strftime("%d-%m-%Y %H:%M:%S"),
                    "logout_time": logout_time_str,
                    "session_duration": session_duration / 3600  # Convert seconds to hours
                })

            # Convert total time (in seconds) to HH:MM:SS format
            hours, remainder = divmod(total_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            total_time_formatted = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
            
            print(f"Total time spent today: {total_time_formatted}")  # Debugging log

            # Return login data and formatted total time
            return JsonResponse({
                "success": True,
                "data": data,
                "total_time": total_time_formatted
            })
        
        return JsonResponse({"success": False, "error": "User ID not provided"})
    
    return JsonResponse({"success": False, "error": "Invalid request"})

@login_required
def user_list(request):
    if request.user.groups.filter(name__in=["Admin", "SuperAdmin"]).exists():
        # Fetch all users excluding superusers (but include the logged-in Admin)
        superadmin_group = Group.objects.get(name='Superadmin')
        users = User.objects.exclude(groups=superadmin_group)

        today = timezone.now().date()

        
        # Add the latest login and logout time to each user
        for user in users:
            latest_login = LoginHistory.objects.filter(user=user, login_time__isnull=False).order_by('-login_time').first()
            latest_logout = LoginHistory.objects.filter(user=user, logout_time__isnull=False).order_by('-logout_time').first()

            # Dynamically add latest login and logout to the user instance
            user.latest_login = latest_login.login_time if latest_login else None
            user.latest_logout = latest_logout.logout_time if latest_logout else None

              # Calculate total logged-in hours for today
            today_logins = LoginHistory.objects.filter(
                user=user,
                login_time__date=today
            )

            total_seconds = 0
            for record in today_logins:
                if record.logout_time:
                    total_seconds += (record.logout_time - record.login_time).total_seconds()

            user.total_hours_today = round(total_seconds / 3600, 2)  # Convert to hours and round
        
        # Render the user list page with the users and their login/logout times
        return render(request, 'user_list.html', {'users': users})
    else:
        # Redirect non-superusers or show a permission denied message
        return JsonResponse({'error': 'Permission Denied'}, status=403)
    
def userprofile(req):
    # Retrieve or create the user profile
    user_profile, created = UserProfile.objects.get_or_create(user=req.user)
 
    if req.method == 'POST':
        print("Image upload initiated")
        # Handle the image upload or other POST actions here
        return render(req, "user_profile.html", {"user_profile": user_profile})
 
    # For GET requests, render the user profile page
    return render(req, "user_profile.html", {"user_profile": user_profile})
 
 
 
@login_required
def upload_profile_image(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
 
    if request.method == 'POST' and 'image' in request.FILES:
        image = request.FILES['image']
        extension = os.path.splitext(image.name)[1].lower()
        allowed_extensions = ['.jpg', '.jpeg', '.png']
 
        # Check if the file extension is allowed
        if extension not in allowed_extensions:
            return JsonResponse({
                'status': 'error',
                'message': "Only JPG, JPEG, and PNG files are allowed."
            })
 
        user_profile.image = image
        user_profile.save()
        # return JsonResponse({'status': 'success', 'message': 'Image uploaded successfully!'})
 
    return redirect("userprofile")
 
 
@login_required
def delete_profile_image(request):
    print("Delete request received")
    if request.method == 'POST':
        user_profile = UserProfile.objects.get(user=request.user)
        user_profile.image.delete(save=False)
        user_profile.image = None
        user_profile.save()
        return redirect('userprofile')
    
def generate_meeting_topic():
    # Get the last event in the database
    last_event = Event.objects.order_by('id').last()

    # If no event exists, start with "Meeting-0001"
    if not last_event:
        return "Meeting-0001"

    # Extract the topic from the last event
    last_topic = last_event.topic

    # Ensure the topic follows the expected format
    try:
        # Split the topic and extract the number part
        number = int(last_topic.split('-')[1]) + 1
    except (IndexError, ValueError):
        # Handle cases where the format is unexpected
        return "Meeting-0001"

    # Return the new topic with zero-padded number
    return f"Meeting-{number:04d}"


def meeting(request):
    topic = generate_meeting_topic()
    print("Generated Topic:", topic)  # Debugging line
    users = User.objects.all()  # Fetch all users

    # Ensure the topic is passed correctly to the template
    return render(request, 'meeting.html', {'topic': topic, 'users': users})

def meetingsave(request):
    if request.method == "POST":
        topic = request.POST.get('topic')
        organiser = request.POST.get('organiser')
        partner = request.POST.get('partner')
        partner_logo = request.POST.get('partner_logo')
        event_type = request.POST.get('type')
        participants = request.POST.getlist('participants')  # Get list of selected users
        location = request.POST.get('location')
        event_date = request.POST.get('date')  # Use this as both from_date and to_date
        starttime = request.POST.get('starttime')
        endtime = request.POST.get('endtime')
        link = request.POST.get('link')
        agenda = request.POST.getlist('agenda[]')
        priority = request.POST.get('priority')


        # Create a Project for the meeting
        default_user = get_object_or_404(User, username='Punithan')
        project = Project(
            projectname=topic,
            priority=priority,
            from_date=event_date,  # Use Event Date for from_date
            to_date=event_date,    # Use Event Date for to_date
            assigned_by=request.user,
            user=None,
        )
        project.save()

         # Create the Event instance
        event = Event(
            topic=topic,
            organiser=organiser,
            partner=partner,
            partner_logo=partner_logo,
            event_type=event_type,
            participants=",".join(participants),  # Store as comma-separated string
            location=location,
            date=event_date,
            starttime=starttime,
            endtime=endtime,
            link=link,
            agenda=agenda,
            project=project,
            prepared_by=request.user,
        )
        event.save()

        return redirect('meeting_list')

    return render(request, 'meeting.html')

def calculate_time_duration(start_time, end_time):
    """
    Calculate the duration between two times, accounting for cross-midnight scenarios.
    """
    start_datetime = datetime.combine(datetime.min, start_time)
    end_datetime = datetime.combine(datetime.min, end_time)
    if end_datetime < start_datetime:
        end_datetime += timedelta(days=1)
    return end_datetime - start_datetime

def meeting_list(request):
    meetings = Event.objects.all()
    return render(request, 'meeting_list.html', {'meetings': meetings})

#sends the meeting invitation using sending.html
def meetingsend(request, id):
    try:
        # Retrieve the event using the given id
        event = Event.objects.get(id=id)
    except Event.DoesNotExist:
        return render(request, 'meeting.html', {"error": "Event not found"})

    try:
        # Extract participant IDs and filter users accordingly
        participant_ids = [int(pid) for pid in event.participants.split(",")]
    except ValueError:
        return render(request, 'meeting.html', {"error": "Invalid participant IDs format"})

    users = User.objects.filter(id__in=participant_ids)

    # Create a list of email addresses for the participants
    to_email = [user.email for user in users]

    # Prepare context for the email body
    context = {
        'topic': event.topic,
        'organiser': event.organiser,
        'partner': event.partner,
        'partner_logo': event.partner_logo,
        'type': event.event_type,
        'location': event.location,
        'date': event.date,
        'starttime': event.starttime,
        'endtime': event.endtime,
        'duration': event.duration,
        'link': event.link,
        'agenda': event.agenda,
    }

    # Render the HTML content for the email
    html_content = render_to_string('sending.html', context)

    # Email details
    subject = f"Meeting Invitation: {event.topic}"
    from_email = "taskaccsys@gmail.com"
    
    # Sending the email to the participants
    email = EmailMultiAlternatives(subject, "", from_email, to_email)
    email.attach_alternative(html_content, "text/html")
    
    try:
        # Send the email to all participants
        email.send()
    except Exception as e:
        # Handle error if sending fails
        return render(request, 'meeting.html', {"error": f"Error sending email: {str(e)}"})

    # Redirect to the meeting list page after sending the email
    return redirect('meeting_list')

def after_meeting(request, id):
    meeting = Event.objects.get(id=id)
    return render(request, 'add_remark.html', {'meeting': meeting})

def delete_meeting(request, id):

    meeting = get_object_or_404(Event, id=id)
    meeting.delete()
    messages.success(request, 'Meeting deleted successfully!')
    return redirect('meeting_list')

def points_discussed(request, id):
    if request.method == 'POST':
        meeting = get_object_or_404(Event, id=id)

        meeting.actual_starttime  = request.POST.get('actual_starttime')
        meeting.actual_endtime = request.POST.get('actual_endtime')
        remarks = request.POST.getlist('remark[]')
        try:
            formatted_actual_start_time = datetime.strptime(meeting.actual_starttime, "%H:%M").time()
            formatted_actual_end_time = datetime.strptime(meeting.actual_endtime, "%H:%M").time()
        except ValueError:
            return render(request, 'meeting.html', {"error": "Invalid time format. Use HH:MM."}) 
        
        meeting.actual_duration = calculate_time_duration(formatted_actual_start_time, formatted_actual_end_time)

        filtered_remarks = [remark.strip() for remark in remarks if remark.strip()] 
        meeting.remark = filtered_remarks  
        meeting.save()

        return redirect('meeting_list')

def points_agreed(request, id):
    meeting = get_object_or_404(Event, id=id)

    if request.method == 'POST':
        # Retrieve form data
        remark = request.POST.get('remark')
        selected_user_ids = request.POST.getlist('selected_users')
        priority = request.POST.get('priority', 'Low')
        assigned_date = request.POST.get('assigned_date')
        final_date = request.POST.get('final_date')
        description = request.POST.get('description', '')

        # Convert dates
        try:
            assigned_date = datetime.strptime(assigned_date, "%Y-%m-%d").date()
            final_date = datetime.strptime(final_date, "%Y-%m-%d").date()
        except ValueError:
            return HttpResponse("Invalid date format. Please use YYYY-MM-DD.", status=400)

        # Get selected users
        selected_users = User.objects.filter(id__in=selected_user_ids)

        if not selected_users:
            messages.error(request, "Please select at least one user to assign the task.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        # Fetch the linked project
        project = meeting.project
        if not project:
            messages.error(request, "No project linked to this meeting.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        # Create tasks and send notifications
        for user in selected_users:
            # Create the task
            task = Task.objects.create(
                taskname=remark,
                priority=priority,
                from_date=assigned_date,
                to_date=final_date,
                description=description,
                user=user,
                project=project,
                assigned_by=request.user
            )

            # Notify user in-app
            Notification.objects.create(
                user=user,
                message=f"Task '{remark}' created by {request.user.username}",
                assigned_by=request.user
            )

            # Send email notification
            if user.email:
                subject = f"New Task Assigned: {remark}"
                message = (
                    f"Dear {user.username},\n\n"
                    f"You have been assigned a new task in the project '{project.projectname}'.\n\n"
                    f"Task Name: {remark}\n"
                    f"Priority: {priority}\n"
                    f"Assigned Date: {assigned_date}\n"
                    f"Final Date: {final_date}\n"
                    f"Description: {description}\n\n"
                    f"Best regards,\n"
                    f"{request.user.username}"
                )
                try:
                    send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email], fail_silently=False)
                except Exception as e:
                    # Log or handle email-sending error
                    messages.error(request, f"Failed to send email to {user.username}: {str(e)}")

        # Redirect back to the referring page
        return redirect(request.META.get('HTTP_REFERER', '/'))

    # GET request: Render the form
    assigned_remarks = [task.taskname for task in meeting.project.tasks.all()] if meeting.project else []
     # Parse participants into a list of user IDs
    participants_ids = list(map(int, meeting.participants.split(','))) if meeting.participants else []

    # Fetch users from the participants
    participants = User.objects.filter(id__in=participants_ids).exclude(groups__name="Superadmin")

    return render(request, 'assign_tasks.html', {
        'meeting': meeting,
        'remarks': meeting.remark,
        'assigned_remarks': assigned_remarks,
        'users': participants  
    })

def minutes_of_meeting(request, id):
    # Fetch the Event object
    meeting = get_object_or_404(Event, id=id)
    
    # Fetch tasks related to the project's tasks
    tasks = Task.objects.filter(project=meeting.project)  # Use the project to filter tasks
    
    # Convert participant IDs into user names
    participant_ids = meeting.participants.split(",")  # Split IDs stored as "1,2,12"
    participants = User.objects.filter(id__in=participant_ids)  # Fetch user objects
    
    # Pass the data to the template
    return render(request, 'minutes_of_meeting.html', {
        'meeting': meeting,
        'tasks': tasks,
        'participants': participants,
    })

def send_mom(request, id):
    # Fetch the Event object
    meeting = get_object_or_404(Event, id=id)
    
    # Fetch associated tasks from the Task table
    tasks = Task.objects.filter(project=meeting.project)  # Use project to filter tasks

    # Get participants' email addresses
    participant_ids = meeting.participants.split(",")  # Split participant IDs into a list
    participants = User.objects.filter(id__in=participant_ids)  # Fetch user objects
    print("participants",participants)
    to_email = [user.email for user in participants if user.email]  # Get their email addresses

    if not to_email:
        return HttpResponse("No participants with valid email addresses found.")

    # Prepare email context
    context = {
        'meeting': {
            'topic': meeting.topic,
            'organiser': meeting.organiser,
            'partner': meeting.partner,
            'event_type': meeting.event_type,
            'participants': participants,
            'location': meeting.location,
            'date': meeting.date,
            'starttime': meeting.starttime,
            'endtime': meeting.endtime,
            'actual_starttime': meeting.actual_starttime,
            'actual_endtime': meeting.actual_endtime,
            'duration': meeting.duration,
            'actual_duration': meeting.actual_duration,
            'agenda': meeting.agenda,
            'remark': meeting.remark,
            'link': meeting.link,
        },
        'tasks': tasks,
    }

    # Render the HTML content
    html_content = render_to_string('sending_mom.html', context)

    # Prepare email
    subject = f"Minutes of the Meeting - {meeting.topic}"
    from_email = "taskaccsys@gmail.com"  # Replace with your email
    email = EmailMultiAlternatives(subject, "", from_email, to_email)
    email.attach_alternative(html_content, "text/html")

    # Send the email
    try:
        email.send()
        return redirect('meeting_list')
    except Exception as e:
        return HttpResponse(f"Failed to send email: {str(e)}")



