import os
import time
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'accsystool.settings')  # Replace with your project's name
django.setup()

from workflow_management.views import fetch_and_forward_replies  # Import from views.py

def periodic_task():
    """
    Function to periodically call fetch_and_forward_replies().
    """
    while True:
        try:
            print("Running fetch_and_forward_replies...")
            fetch_and_forward_replies()
            print("Task completed. Sleeping for 60 seconds.")
        except Exception as e:
            print(f"Error occurred: {e}")
        
        # Wait for 60 seconds before the next execution
        time.sleep(60)

if __name__ == "__main__":
    periodic_task()
