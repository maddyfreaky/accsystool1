from django.core.management.base import BaseCommand
from workflow_management.utils import fetch_and_forward_replies  # Import your function

class Command(BaseCommand):
    help = "Fetch and forward replies from Gmail to the original sender"

    def handle(self, *args, **kwargs):
        fetch_and_forward_replies()
        self.stdout.write("Replies fetched and forwarded successfully.")
