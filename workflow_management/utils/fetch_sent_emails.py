import email, imaplib
from email.header import decode_header
from django.conf import settings
from workflow_management.models import SentEmail


def fetch_sent_emails(user_email):
    # Connect to the server
    print("to",user_email)
    mail = imaplib.IMAP4_SSL('imap.gmail.com')  # Use settings from your provider
    mail.login(settings.IMAP_USER, settings.IMAP_PASSWORD)
    
    # Select the "Sent Mail" folder
    mail.select('"[Gmail]/Sent Mail"')  # This is Gmail's "Sent Mail"; adjust for other providers
    
    # Search for emails sent to the specific user
    status, messages = mail.search(None, f'TO "{user_email}"')
    
    # Fetch the emails
    email_ids = messages[0].split()
    emails = []
    
    for email_id in email_ids:
        print("from",email_id)
        # Fetch email by ID
        res, msg_data = mail.fetch(email_id, '(RFC822)')
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                # Parse email content
                msg = email.message_from_bytes(response_part[1])
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")
                from_ = msg.get("From")
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain" and "attachment" not in str(part.get("Content-Disposition")):
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = msg.get_payload(decode=True).decode()
                
                # Append to emails list
                emails.append({
                    "from": from_,
                    "subject": subject,
                    "body": body,
                    "date": msg.get("Date"),
                })
    # Logout
    mail.logout()
    return emails

def fetch_replies():
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(settings.IMAP_USER, settings.IMAP_PASSWORD)
    mail.select("inbox")

    status, messages = mail.search(None, "ALL")
    email_ids = messages[0].split()
    replies = []

    for email_id in email_ids:
        res, msg_data = mail.fetch(email_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject = msg["Subject"]
                
                # Check for unique identifier
                if "[Ref:" in subject:
                    ref_id = subject.split("[Ref:")[1].split("]")[0]
                    original_email = SentEmail.objects.filter(message_id=ref_id).first()
                    if original_email:
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    body = part.get_payload(decode=True).decode()
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode()
                        
                        replies.append({
                            "original_email": original_email,
                            "reply_body": body,
                            "reply_from": msg.get("From"),
                            "reply_date": msg.get("Date"),
                        })
    mail.logout()
    return replies
