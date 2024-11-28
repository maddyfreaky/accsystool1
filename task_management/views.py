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
from django.utils.timezone import localtime
from django.contrib.auth.models import Group




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


def user_project(request, user_id):
    print("user_project function")

    # Get the user by ID or return 404 if not found
    user = get_object_or_404(User, id=user_id)

    # Filter out projects associated with users in the SuperAdmin group
    user_projects = Project.objects.exclude(user__groups__name='SuperAdmin').order_by('-created_at')
    print("Filtered user_projects (excluding SuperAdmin projects):", user_projects)

    context = {
        'user': user,  # Pass the selected user
        'projects': user_projects,  # Pass the filtered projects for this user
    }

    return render(request, 'user_project.html', context)





def create_project(request, user_id):
    print("create pgt function")
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        # Get form data from POST request
        projectname = request.POST.get('projectname')
        taskname = request.POST.get('taskname')
        priority = request.POST.get('priority')
        from_date = request.POST.get('fromdate')
        to_date = request.POST.get('todate')
        if Project.objects.filter(projectname=projectname).exists():
            return JsonResponse({'status': 'error', 'message': 'Project name already exists, please give a different name'})

        try:
            print("try block")
            # Create and save new Project instance, linking it to the user
            project = Project(
                projectname=projectname,
                # taskname=taskname,
                priority=priority,
                from_date=from_date,
                to_date=to_date,
                user=user,  # Associate the project with the selected user
                assigned_by=request.user  # Set the user creating the project

            )
            project.save()
            print(" project data saved")

            # Redirect back to the user's project page
            return redirect('user_project', user_id=user.id)

        except Exception as e:
            print("except")
            return HttpResponse(f"An error occurred: {e}", status=500)

    # If GET request, just render the page with the user's existing projects
    projects = Project.objects.filter(user=user)
    return render(request, 'userproject.html', {'projects': projects, 'user': user})

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
            
            # Update the task's status and save it to the database
            task.status = new_status
            task.save()

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

        if status in dict(Task.STATUS_CHOICES).keys():
            task.status = status
            task.save()

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

def task_detail(request, project_id, user_id):
    project = Project.objects.get(id=project_id)
    selected_user = User.objects.get(id=user_id)
    tasks = Task.objects.filter(project=project, user=selected_user)  # Fetch tasks for the specific user

    # Fetch all tasks related to this project for parent task dropdown
    all_tasks = Task.objects.filter(project=project)
    superadmin_group = Group.objects.get(name='Superadmin')
    excluded_users = User.objects.filter(groups=superadmin_group) | User.objects.filter(id=user_id)
    available_users = User.objects.exclude(id__in=excluded_users.values_list('id', flat=True))

    return render(request, 'task_detail.html', {
        'tasks': tasks,
        'selected_project': project,
        'user': selected_user,
        'all_tasks': all_tasks,  # Passing all tasks for parent task selection
        'available_users': available_users
    })


from django.contrib.auth.models import User

from django.core.mail import send_mail
from django.conf import settings

def create_task(request, project_id, user_id):
    if request.method == 'POST':
        project = get_object_or_404(Project, id=project_id)
        assigning_user = get_object_or_404(User, id=user_id)  # User creating the task

        taskname = request.POST.get('taskname')
        priority = request.POST.get('priority')
        from_date = request.POST.get('fromdate')
        to_date = request.POST.get('todate')
        description = request.POST.get('description')
        is_child = request.POST.get('is_child') == 'on'
        parent_task_id = request.POST.get('parent_task')

        # Get selected users
        selected_user_ids = request.POST.getlist('selected_users')
        selected_users = User.objects.filter(id__in=selected_user_ids)

        # Add the user specified in the URL
        selected_users = list(selected_users)  # Convert to list
        main_user = get_object_or_404(User, id=user_id)
        if main_user not in selected_users:
            selected_users.append(main_user)  # Ensure the main user is included

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
                    f"This is a system generated email, please do not reply"
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

        return redirect('task_detail', project_id=project.id, user_id=user_id)

    
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
    # Get the Normaluser group
    normal_user_group = Group.objects.get(name='Normalusers')

    # Check if the logged-in user is in the Admin group
    if request.user.groups.filter(name='Admin').exists():
        # Get both Admin and Superadmin groups
        admin_group = Group.objects.get(name='Admin')
        superadmin_group = Group.objects.get(name='Superadmin')

        # Show projects where assigned_by is either Admin or Superadmin, and the project is assigned to Normalusers
        projects = Project.objects.filter(
            user__groups=normal_user_group
        ).filter(
            assigned_by__groups__in=[admin_group, superadmin_group]
        ).order_by('-created_at')
    
    else:
        # For other users (Superadmin and others), exclude their own projects
        projects = Project.objects.exclude(user=request.user).order_by('-created_at')

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

        # Iterate over each project to get tasks specific to the logged-in user
        for project in projects:
            # Filter tasks for the logged-in user
            tasks = project.tasks.filter(user=request.user)

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
            
            context = {
                'projects': projects,
                'tasks': tasks,  # Pass the filtered tasks to the template
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