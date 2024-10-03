from django.http import JsonResponse
from django.utils.dateformat import format
from django.utils import timezone
from .models import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.timesince import timesince
from django.views.decorators.http import require_POST
from django.urls import reverse
import re
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

    # Retrieve projects that have tasks assigned to the logged-in user
    projects = Project.objects.filter(tasks__user=request.user).distinct().order_by('-created_at')

    # Status choices for dropdown display
    status_choices = Project.STATUS_CHOICES

    return render(request, 'todopage.html', {'projects': projects, 'status_choices': status_choices})

def todopgt(request):
     print("pgt function")
     if request.method == 'POST':
        projectname = request.POST.get('projectname')
        projectenddate = request.POST.get('projectdate')
        projectstatus = request.POST.get('projectpriority')

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
    if request.user.is_superuser:  # Check if the logged-in user is an admin (superuser)
        users = User.objects.exclude(is_superuser=True).exclude(id=request.user.id)
        return render(request, 'user_list.html', {'users': users})
    else:
        # Redirect non-superusers or show a permission denied message
        return JsonResponse({'error': 'Permission Denied'}, status=403)


def user_project(request, user_id):
    print("user_project function")
    # Get the user by ID or return 404 if not found
    user = get_object_or_404(User, id=user_id)

    # Get all projects associated with the specific user
    user_projects = Project.objects.all().order_by('-created_at')
    print("this is the user_projects",user_projects)
    context = {
        'user': user,  # Pass the selected user
        'projects': user_projects,  # Pass the projects for this user
    }

    return render(request, 'user_project.html', context)


@login_required
def delete_user(request, user_id):
    if request.user.is_superuser:
        user = get_object_or_404(User, id=user_id)
        user.delete()
        return JsonResponse({'success': 'User deleted successfully.'})  # Return JSON response on successful deletion
    else:
        return JsonResponse({'error': 'Permission Denied'}, status=403)  # Return error response if user is not superuser

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
        return redirect('user_project', user_id=project.user.id)
    
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

    # Redirect to the all_projects_with_tasks URL
    return redirect('all_projects_with_tasks')  # Adjust to your actual URL name
    
def specific_user_tasks_view(request, project_id):
    # Retrieve the project based on the project ID
    project = Project.objects.get(id=project_id)

    # Retrieve tasks for this project that are assigned to the logged-in user
    tasks = Task.objects.filter(project=project, user=request.user)

    context = {
        'project': project,
        'tasks': tasks
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

        # Create a new task object
        task = Task(
            taskname=taskname,
            priority=priority,
            from_date=from_date,
            to_date=to_date,
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
    tasks = Task.objects.filter(project=project, user=selected_user)  # Fetch tasks for specific user
    return render(request, 'task_detail.html', {'tasks': tasks, 'selected_project': project, 'user': selected_user})


def create_task(request, project_id, user_id):
    if request.method == 'POST':
        project = get_object_or_404(Project, id=project_id)
        user = get_object_or_404(User, id=user_id)

        taskname = request.POST.get('taskname')
        priority = request.POST.get('priority')
        from_date = request.POST.get('fromdate')
        to_date = request.POST.get('todate')
        description = request.POST.get('description')  # Get description from form

        # Create the task with the specific project and user
        Task.objects.create(
            taskname=taskname,
            priority=priority,
            from_date=from_date,
            to_date=to_date,
            project=project,
            user=user,
            description=description,  # Save the description
        )

        return redirect('task_detail', project_id=project.id, user_id=user.id)    
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
            # Filter tasks for the logged-in user only
            tasks = project.tasks.filter(user=request.user)
            if tasks.exists():
                user_tasks.append({
                    'project': project,
                    'tasks': tasks
                })
            print(f"Tasks for {project.projectname} assigned to {request.user.username}: {tasks}")

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
    user = request.user  # Get the logged-in user
    
    # Filter tasks based on the logged-in user
    todo_tasks_custom = Task.objects.filter(user=user, status='Not Started')
    in_progress_tasks_custom = Task.objects.filter(user=user, status='Working')
    completed_tasks_custom = Task.objects.filter(user=user, status='Completed')
    
    context = {
        'todo_tasks_custom': todo_tasks_custom,
        'in_progress_tasks_custom': in_progress_tasks_custom,
        'completed_tasks_custom': completed_tasks_custom,
    }
    
    return render(request, 'usercard.html', context)

@csrf_exempt
def get_comments(request, task_id):
    comments = Comment.objects.filter(task_id=task_id).values('text', 'comment_timestamp')

    comments_list = [
        {'text': comment['text'], 'timestamp': comment['comment_timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
        for comment in comments
    ]

    return JsonResponse({'success': True, 'comments': comments_list})


@csrf_exempt
def add_comment(request, task_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        comment_text = data.get('comment')

        task = Task.objects.get(id=task_id)
        new_comment = Comment.objects.create(task=task, text=comment_text)
        new_comment.save()

        return JsonResponse({'success': True, 'comment': new_comment.text, 'timestamp': new_comment.comment_timestamp.strftime('%Y-%m-%d %H:%M:%S')})
    return JsonResponse({'success': False, 'message': 'Invalid request'})