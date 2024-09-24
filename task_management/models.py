from django.db import models
from django.contrib.auth.models import User
from tinymce import models as tinymce_models
from django.utils import timezone



class Project(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('working', 'Working'),
        ('pending_review', 'Pending Review'),
        ('overdue', 'OverDue'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('not_started', 'Not Started'),

    ]

    projectname = models.CharField(max_length=200)
    taskname = models.CharField(max_length=200, null=True, blank=True)

    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES,null=True, blank=True)
    from_date = models.DateField(null=True, blank=True)  # Allow null temporarily
    to_date = models.DateField(null=True, blank=True)    # Allow null temporarily
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='assigned_projects', null=True, blank=True)  # Link to the User model
    # The user who assigned the project (admin/superuser)
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_projects',null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')

 



    def _str_(self):
        return self.projectname

class Issue(models.Model):
    project = models.ForeignKey(Project, related_name='issues', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically sets the time when an issue is created
    completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)  # Automatically updates when saved
    



    def _str_(self):
        return self.title

class Todolist(models.Model):
    STATUS_CHOICES = [
        ('todo', 'TO DO'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='details')
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='todolists', blank=True, null=True)  # Use string reference for Task
    description = tinymce_models.HTMLField()  # TinyMCE field for rich text
    comments = tinymce_models.HTMLField(blank=True, null=True)
    attached_file = models.FileField(upload_to='todoattachments/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')

    def __str__(self):
        return f"Details for {self.project.projectname} - Task: {self.task.name}"
    
class Task(models.Model):
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('Not Started', 'Not Started'),
        ('Working', 'Working'),
        ('Completed', 'Completed'),
    ]

    taskname = models.CharField(max_length=255)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Low')
    from_date = models.DateField()
    to_date = models.DateField()
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='Not Started')  # Added status field


    # Establishing relationships
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.taskname} - {self.priority}"
    
class TodolistFile(models.Model):
    todolist = models.ForeignKey(Todolist, on_delete=models.CASCADE, related_name='files')  # Related to Todolist
    attached_file = models.FileField(upload_to='todoattachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.attached_file.name
    
