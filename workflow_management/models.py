from django.db import models
from django.contrib.auth.models import User

class LeaveRequest(models.Model):
    LEAVE_TYPE_CHOICES = [
        ('Loss Of pay', 'Loss Of pay'),
        ('Comp-Off', 'Comp-Off'),
        ('Sick Leave probation', 'Sick Leave probation'),
        ('Optional Holiday', 'Optional Holiday'),
    ]
    
    SESSION_CHOICES = [
        ('Session 1', 'Session 1'),
        ('Session 2', 'Session 2'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)  # The requester
    leave_type = models.CharField(max_length=50, choices=LEAVE_TYPE_CHOICES)
    from_date = models.DateField()
    to_date = models.DateField()
    session_from = models.CharField(max_length=50, choices=SESSION_CHOICES)
    session_to = models.CharField(max_length=50, choices=SESSION_CHOICES)
    reason = models.TextField()
    file = models.FileField(upload_to='leave_attachments/', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    # Track current approval level
    current_level = models.IntegerField(default=1)  # Start from Level 1

    # Track selected approvers for each level
    level1_approvers = models.ManyToManyField(User, related_name='level1_leave_requests', blank=True)
    level2_approvers = models.ManyToManyField(User, related_name='level2_leave_requests', blank=True)
    level3_approvers = models.ManyToManyField(User, related_name='level3_leave_requests', blank=True)
    rejection_reason = models.TextField(blank=True, null=True)  # This field will store the rejection reason

    def __str__(self):
        return f"{self.leave_type} from {self.from_date} to {self.to_date} for {self.user.username}"
