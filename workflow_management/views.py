
from django.http import HttpResponse

# Create your views here.



from django.shortcuts import render,redirect, get_object_or_404
from django.views import View
from .models import *
from django.views.generic import TemplateView
from django.contrib.auth.models import User
from django.http import JsonResponse
import os, mimetypes, json
from django.contrib.auth.models import User, Group
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin




def workflowmgt(request):
    return render(request, 'components.html')  

def workflow(request):
    return render(request,"workflow.html")




from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db.models import Q

from django.db.models import Q
from django.utils import timezone

class LeaveRequestView(View):
    allowed_file_types = ['pdf', 'xls', 'xlsx', 'doc', 'docx', 'ppt', 'pptx', 'jpg', 'jpeg', 'png', 'txt']

    def get(self, request, *args, **kwargs):
        # Your leave requests only (submitted by you)
        user_leave_requests = LeaveRequest.objects.filter(user=request.user).order_by('-created_at')

        # Leave requests pending your approval (not created by you)
        pending_approval_requests = LeaveRequest.objects.filter(
            status="Pending",
            current_level__in=[1, 2, 3]
        ).exclude(user=request.user).filter(
            Q(level1_approvers=request.user, current_level=1, status="Pending") |
            Q(level2_approvers=request.user, current_level=2, status="Pending") |
            Q(level3_approvers=request.user, current_level=3, status="Pending")
        ).distinct().order_by('-created_at')

        # Calculate number of days for each leave request
        for leave_request in user_leave_requests:
            if leave_request.from_date and leave_request.to_date:
                leave_request.no_of_days = (leave_request.to_date - leave_request.from_date).days + 1
            else:
                leave_request.no_of_days = 0

        for leave_request in pending_approval_requests:
            if leave_request.from_date and leave_request.to_date:
                leave_request.no_of_days = (leave_request.to_date - leave_request.from_date).days + 1
            else:
                leave_request.no_of_days = 0

        context = {
            'user_leave_requests': user_leave_requests,
            'pending_approval_requests': pending_approval_requests,
            'level1_users': User.objects.filter(groups__name='Level1'),
            'level2_users': User.objects.filter(groups__name='Level2'),
            'level3_users': User.objects.filter(groups__name='Level3'),  # Only pending requests for your approval
        }

        return render(request, 'leavedetails.html', context)
        
    def post(self, request, *args, **kwargs):
        # Handling file validation
        file = request.FILES.get('file')
        max_file_size = 5 * 1024 * 1024
        if file:
            extension = os.path.splitext(file.name)[1][1:].lower()
            if extension not in self.allowed_file_types:
                return JsonResponse({
                    'status': 'error',
                    'message': f"File type not allowed. Allowed types: {', '.join(self.allowed_file_types)}"
                })
        if file!=None:

            if file.size > max_file_size:
                return JsonResponse({
                    'status': 'error',
                    'message': "File size exceeds the 5 MB limit."
                })

        # Save the leave request
        leave_request = LeaveRequest.objects.create(
            user=request.user,
            leave_type=request.POST.get('LeaveType'),
            from_date=request.POST.get('fromdate'),
            to_date=request.POST.get('todate'),
            session_from=request.POST.get('Session1'),
            session_to=request.POST.get('Session2'),
            reason=request.POST.get('Reason'),
            file=file,
            status='Pending',
            created_at=timezone.now(),
            current_level=1
        )

        # Assign approvers and notify them
        for level, field_name in enumerate(['level1_users[]', 'level2_users[]', 'level3_users[]'], start=1):
            user_ids = request.POST.getlist(field_name)
            users = User.objects.filter(id__in=user_ids)
            getattr(leave_request, f'level{level}_approvers').set(users)
            if level == 1:  # Notify Level 1 approvers
                self.notify_approvers(users, leave_request)

        return JsonResponse({'status': 'success', 'message': 'Leave applied successfully!'})

    def notify_approvers(self, approvers, leave_request):
        subject = f"Leave Request Approval Needed from {leave_request.user.username}"
        message = (
            f"A leave request from {leave_request.user.username} requires your approval.\n\n"
            f"Leave Type: {leave_request.leave_type}\n"
            f"From: {leave_request.from_date}\n"
            f"To: {leave_request.to_date}\n"
            f"Reason: {leave_request.reason}\n"
        )
        email = EmailMessage(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [approver.email for approver in approvers]
        )
        try:
            email.send(fail_silently=False)
        except Exception as e:
            print(f"Failed to send email: {e}")

@csrf_exempt
def approve_leave(request, leave_id):
    leave_request = get_object_or_404(LeaveRequest, id=leave_id)
    approvers, next_level_users = None, None
    
    # Determine current level approvers and next level approvers
    if leave_request.current_level == 1:
        approvers = leave_request.level1_approvers.all()
        next_level_users = leave_request.level2_approvers.all()
    elif leave_request.current_level == 2:
        approvers = leave_request.level2_approvers.all()
        next_level_users = leave_request.level3_approvers.all()
    elif leave_request.current_level == 3:
        approvers = leave_request.level3_approvers.all()

    # Check if the user is authorized to approve at the current level
    if request.user not in approvers:
        return JsonResponse({'status': 'error', 'message': 'You are not authorized to approve this request.'})

    # Update leave request's current level or mark as Approved if at the final level
    if leave_request.current_level < 3:
        leave_request.current_level += 1
        leave_request.status = 'Pending'
        leave_request.save()
        
        # Notify the next level approvers if there are any
        if next_level_users:
            LeaveRequestView().notify_approvers(next_level_users, leave_request)
        # messages.success(request, "Leave request moved to the next approval level.")
    else:
        # Mark as Approved when all levels have approved
        leave_request.status = 'Approved'
        leave_request.save()
        # messages.success(request, "Leave request approved successfully.")

   
    return JsonResponse({'status': 'success', 'message': 'Leave request approved successfully.'})

def reject_leave(request, leave_id):
    leave_request = get_object_or_404(LeaveRequest, id=leave_id)

    if request.method == 'POST':
        # Get the rejection reason from the request data (from the JavaScript AJAX POST request)
        data = json.loads(request.body)  # Extracting data sent by the frontend (JSON)
        reason = data.get('Reason')

        if reason:
            # Save the reason and update the leave status to 'Rejected'
            leave_request.rejection_reason = reason  # Assuming 'reason' field exists in the model
            leave_request.status = 'Rejected'
            leave_request.save()

            

            # Add a success message to notify that the leave request was rejected
            messages.success(request, "Leave request rejected successfully.")
            print("leave rejected")
             # Send email notification to the user
            subject = "Your Leave Request has been Rejected"
            message = f"Dear {leave_request.user.username},\n\nYour leave request has been rejected.\nReason: {reason}\n\nThank you."
            recipient = leave_request.user.email

            try:
                send_mail(subject, message, settings.EMAIL_HOST_USER, [recipient])
            except Exception as e:
                print(f"Failed to send email: {e}")
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Reason is required'})
      # Handle GET request (show the leave request details)

class WithdrawLeaveView(LoginRequiredMixin, View):
    def post(self, request, leave_id):
        print("Withdrawal function called")
        
        # Fetch the leave request based on the leave_id
        leave_request = get_object_or_404(LeaveRequest, id=leave_id, user=request.user)
        print("Processing POST request")

        # Delete the leave request
        leave_request.delete()

        return JsonResponse({'status': 'success', 'message': 'Leave request withdrawn successfully.'})
    
    def get(self, request, leave_id):
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})