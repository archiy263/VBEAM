import base64
import re
from email.mime.text import MIMEText
# from modules.voice import speak, listen
from modules.contacts import get_email

# EMAIL MESSAGE CREATION

def create_message(to, subject, message_text):

    message = MIMEText(message_text)

    message['to'] = to
    message['subject'] = subject

    raw = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    return {'raw': raw}

# SEND EMAIL USING GMAIL API

def send_email(service, to, subject, body):

    try:

        message = create_message(to, subject, body)

        service.users().messages().send(
            userId="me",
            body=message
        ).execute()

        print("Email sent successfully")

        print(f"Email sent to {to}")

    except Exception as e:

        print("Email sending error:", e)

        print("Failed to send email")

# def reply_latest_email(service,body):

#     if service is None:
#         print("Please login first")
#         return

#     results = service.users().messages().list(
#         userId='me',
#         maxResults=1
#     ).execute()

#     messages = results.get('messages', [])

#     if not messages:
#         print("No emails to reply")
#         return

#     msg = service.users().messages().get(
#         userId='me',
#         id=messages[0]['id'],
#         format='full'
#     ).execute()

#     headers = msg['payload']['headers']

#     sender = ""

#     for header in headers:

#         if header['name'] == 'From':
#             sender = header['value']
#             break

#     print("What is your reply?")

#     # reply = listen()

#     # if not reply:
#     #     print("Reply cancelled")
#     #     return

#     send_email(service, sender, "Re:", body)
def reply_latest_email(service, body):

    if service is None:
        return

    results = service.users().messages().list(
        userId='me',
        maxResults=1
    ).execute()

    messages = results.get('messages', [])

    if not messages:
        return

    msg = service.users().messages().get(
        userId='me',
        id=messages[0]['id'],
        format='full'
    ).execute()

    headers = msg['payload']['headers']

    sender = ""
    subject = ""

    for header in headers:
        if header['name'] == 'From':
            sender = header['value']
        if header['name'] == 'Subject':
            subject = header['value']

    # Extract only email from "Name <email>"
    import re
    match = re.search(r'<(.+?)>', sender)
    if match:
        sender_email = match.group(1)
    else:
        sender_email = sender

    send_email(service, sender_email, "Re: " + subject, body)
def reply_to_contact(service, name, body):

    email = get_email(name)

    if not email:

        print("Contact not found")

        return


    # reply = listen()

    # if not reply:

    #     print("Reply cancelled")

    #     return


    send_email(service, email, "Reply", body)

def normalize_email(spoken_email):

    if not spoken_email:
        return None

    email = spoken_email.lower()

    # Replace speech patterns
    replacements = {
        " at the rate ": "@",
        " at ": "@",
        " dot ": ".",
        " underscore ": "_",
        " dash ": "-",
        " space ": ""
    }

    for key, value in replacements.items():
        email = email.replace(key, value)

    # Remove extra spaces
    email = re.sub(r"\s+", "", email)

    # If user only said username
    if "@" not in email:
        email = email + "@gmail.com"

    # Validate
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return None

    return email

# GET VOICE INPUT WITH RETRY

def get_voice_input(prompt, retries=3):

    for attempt in range(retries):

        print(prompt)

        # text = listen()

        # if text:
        #     return text

        # print("I did not hear properly")

    return None

# MAIN EMAIL FLOW

def send_email_flow(service):

    if service is None:
        print("Please login first")
        return

    # STEP 1 — Recipient
    name = get_voice_input("Tell contact name or email address")

    if not name:
        print("Recipient not provided")
        return

    # Check if contact saved
    email = get_email(name)

    # If not saved, treat as email
    if not email:

        email = normalize_email(name)

        if not email:
            print("Invalid email address")
            return

    # STEP 2 — Subject
    subject = get_voice_input("Tell subject")

    if not subject:
        print("Subject not provided")
        return

    # STEP 3 — Body
    body = get_voice_input("Tell message")

    if not body:
        print("Message not provided")
        return

    # CONFIRMATION STEP

    print("You are sending email to " + email)
    print("Subject is " + subject)
    print("Message is " + body)
    print("Do you want to send this email? Say yes or no")

    confirmation = listen()

    if not confirmation:
        print("Confirmation not received. Email cancelled")
        return

    if "yes" in confirmation:
        send_email(service, email, subject, body)
        print("Email sent successfully")
    else:
        print("Email cancelled")

    print("\n EMAIL DETAILS ")
    print("To:", email)
    print("Subject:", subject)
    print("Message:", body)
    print("\n")