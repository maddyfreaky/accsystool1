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




# Create your views here.

# def task_management(request):
#     return render(request,'task_management.html')
@login_required
def todlistpage(request):
    print("tolistpage fun")
    # Retrieve all projects, ordered by creation time (most recent first)
    projects = Project.objects.filter(user=request.user).order_by('-created_at')
    status_choices = Project.STATUS_CHOICES

    return render(request, 'todopage.html', {'projects': projects, 'status_choices': status_choices})

def todopgt(request):
     print("pgt function")
     if request.method == 'POST':
        projectname = request.POST.get('projectname')
        print(projectname)
        if projectname:
            print("pgt if")
            # Create and save the project
            Project.objects.create(
                projectname=projectname,
                user=request.user,  # Assign the currently logged-in user
                assigned_by=request.user  # Assign the currently logged-in user as the creator

            )
            print("project saved")
            return redirect('todlistpage')  # Redirect to the project list page after saving
     return render(request,"todolist.html")

@login_required
def projects(request, project_id):
    print("heelo")
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
    if request.method == 'DELETE':
        try:
            project = Project.objects.get(id=project_id)
            project.delete()
            return JsonResponse({'message': 'Project deleted successfully'})
        except Project.DoesNotExist:
            return JsonResponse({'error': 'Project not found'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


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
    user_projects = Project.objects.filter(user=user).order_by('-created_at')
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
                taskname=taskname,
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
def update_task_status(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        task_id = data.get('id')
        new_status = data.get('status')

        try:
            task = Todolist.objects.get(id=task_id)
            task.status = new_status
            task.save()
            return JsonResponse({'success': True})
        except Todolist.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Task not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})

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

def card_update_task_status(request, task_id):
    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id)
        status = request.POST.get('status')
        
        if status in dict(Task.STATUS_CHOICES).keys():
            task.status = status
            task.save()

        return redirect('specific_user_tasks_view', project_id=task.project.id)
    
def specific_user_tasks_view(request, project_id):
    # Get the project by its ID
    print("specific task view")
    project = get_object_or_404(Project, id=project_id)
    
    # Get the tasks related to the project
    tasks = Task.objects.filter(project=project)
    
  

    context = {
        'project': project,
        'tasks': tasks,
        # 'task_counts': task_counts,

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

def project_detail(request, project_id):
    print("vinpoth")
    # Get the project by ID or return 404 if not found
    project = get_object_or_404(Project, id=project_id)

    # Get all tasks for the selected project
    project_tasks = Task.objects.filter(project=project).order_by('-from_date')
    
    # Get all projects for the same user (for retaining the full table if needed)
    user_projects = Project.objects.filter(user=project.user).order_by('-created_at')
    
    context = {
        'selected_project': project,  # Pass the selected project
        'projects': user_projects,    # Pass all projects for the user
        'tasks': project_tasks,       # Pass the tasks related to the selected project
    }

    return render(request, 'task_detail.html', context)


def create_task(request, project_id):
    if request.method == "POST":
        # Get the related project by ID
        project = get_object_or_404(Project, id=project_id)

        # Extract form data
        taskname = request.POST.get('taskname')
        priority = request.POST.get('priority')
        fromdate = request.POST.get('fromdate')
        todate = request.POST.get('todate')

        # Validate the data and create the task object
        if taskname and priority and fromdate and todate:
            # Create a new task and associate it with the specific project
            task = Task.objects.create(
                project=project,
                user=request.user,  # Assign the current logged-in user to the task

                taskname=taskname,
                priority=priority,
                from_date=fromdate,
                to_date=todate,
            )
            task.save()

            # Success message

            # Redirect to the project detail page after saving the task
            return redirect('project_detail', project_id=project.id)
        else:
            # Error message if fields are not filled
            # messages.error(request, 'Please fill all the fields.')

            # Reload the form with the selected project
            return redirect('project_detail', project_id=project.id)

    # In case of GET request, redirect to project detail page
    return redirect('project_detail', project_id=project_id)
