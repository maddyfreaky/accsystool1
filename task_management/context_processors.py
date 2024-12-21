from .models import UserProfile
 
def user_profile(request):
    if request.user.is_authenticated:
        # Retrieve or create the UserProfile if it doesn’t exist
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        return {'user_profile': user_profile}
    return {}