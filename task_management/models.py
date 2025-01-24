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
    # taskname = models.CharField(max_length=200)

    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    from_date = models.DateField(null=True, blank=True)  # Allow null temporarily
    to_date = models.DateField(null=True, blank=True)    # Allow null temporarily
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # New field to store last update tim

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,related_name='assigned_projects')  # Link to the User model
    # The user who assigned the project (admin/superuser)
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_projects')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    # Method to check if all tasks are completed
    def all_tasks_completed(self):
        return self.tasks.filter(status='Completed').count() == self.tasks.count()

    def __str__(self):
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
    
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

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
        ('Pending Review', 'Pending Review'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('Rework', 'Rework'),
    ]

    taskname = models.CharField(max_length=255)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Low')
    from_date = models.DateField()
    to_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Not Started')
    
    description = models.TextField(blank=True)  # Description field

    # Relationships
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='tasks')

    # Field for child task functionality
    is_child = models.BooleanField(default=False)
    parent_task = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='child_tasks')

    # Fields for storing the date and time when status is updated
    status_updated_at = models.DateTimeField(null=True, blank=True)
    updated_as_working = models.DateTimeField(null=True, blank=True)
    updated_as_completed = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    # Field to track who assigned the task
    assigned_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_tasks')

    def save(self, *args, **kwargs):
        # Handle auto-updating the `status_updated_at` timestamp
        if self.pk:
            original_task = Task.objects.get(pk=self.pk)

            # Update `status_updated_at` if the status changes
            if original_task.status != self.status:
                self.status_updated_at = timezone.now()

            # Update `updated_as_working` if the status is set to "Working"
            if self.status == 'Working' and original_task.status != 'Working':
                self.updated_as_working = timezone.now()

            # Update `updated_as_completed` if the status is set to "Completed"
            if self.status == 'Completed' and original_task.status != 'Completed':
                self.updated_as_completed = timezone.now()

        super(Task, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.taskname} - {self.priority}"
    
class TodolistFile(models.Model):
    todolist = models.ForeignKey(Todolist, on_delete=models.CASCADE, related_name='files')  # Related to Todolist
    attached_file = models.FileField(upload_to='todoattachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.attached_file.name
    
class ArchivedProject(models.Model):
        PRIORITY_CHOICES = Project.PRIORITY_CHOICES
        STATUS_CHOICES = Project.STATUS_CHOICES

        projectname = models.CharField(max_length=200)
        taskname = models.CharField(max_length=200)
        priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
        from_date = models.DateField(null=True, blank=True)
        to_date = models.DateField(null=True, blank=True)
        created_at = models.DateTimeField()
        updated_at = models.DateTimeField()
        deleted_at = models.DateTimeField(default=timezone.now)  # Default to current time

        user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='archived_projects')
        assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='archived_created_projects')
        status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')

        def __str__(self):
            return self.projectname

class DeletedTask(models.Model):
    taskname = models.CharField(max_length=255)
    priority = models.CharField(max_length=10)
    from_date = models.DateField()
    to_date = models.DateField()
    deleted_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self):
        return f"Deleted Task: {self.taskname} - {self.priority}"

class Comment(models.Model):
    task = models.ForeignKey(Task, related_name='comments', on_delete=models.CASCADE)
    text = models.TextField()
    comment_timestamp = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')  # Add user field

    def __str__(self):
        return f"Comment on {self.task.title} by {self.user.username} at {self.comment_timestamp}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)  # To track if the notification has been read
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_notifications')  # User who assigned the task


    def _str_(self):
        return f"Notification for {self.user.username}: {self.message}"

class ArchivedUser(models.Model):
    username = models.CharField(max_length=255)
    email = models.EmailField()
    date_joined = models.DateTimeField()
    deleted_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return self.username
    
class LoginHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    login_time = models.DateTimeField(default=timezone.now)
    logout_time = models.DateTimeField(null=True, blank=True)

    def _str_(self):
        return f"{self.user.username} - Login: {self.login_time}, Logout: {self.logout_time}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # mobile = models.BigIntegerField(unique=True,null=True)  # Use BigIntegerField for larger numbers
    image = models.ImageField(upload_to='profile_images/', default='profile_images/default.jpg')  # Profile image field

class Event(models.Model):
    topic = models.CharField(max_length=200)  # Topic of the event
    organiser = models.CharField(max_length=200)
    partner=models.CharField(max_length=200,default='none')
    partner_logo=models.URLField(blank=True, null=True) # Organiser's name
    project = models.OneToOneField(Project, null=True, blank=True, on_delete=models.SET_NULL, related_name='meeting')
    event_type = models.CharField(max_length=100)  # Type of the event
    participants = models.CharField(max_length=500) # Participants' details
    location = models.CharField(max_length=300)  # Location of the event
    date = models.DateField(null=True)  # Event date
    starttime = models.TimeField(null=True)
    endtime = models.TimeField(null=True)
    actual_starttime = models.TimeField(null=True)
    actual_endtime = models.TimeField(null=True)
    duration = models.DurationField(null=True)
    actual_duration = models.DurationField(null=True)  # Duration of the event
    agenda = models.JSONField(default=list)
    remark = models.JSONField(default=list)
    link = models.URLField(blank=True, null=True)
    prepared_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='prepared_by')

    def __str__(self):
        return f"{self.topic} organized by {self.organiser}"
 
