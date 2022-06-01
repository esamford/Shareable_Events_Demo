"""
Tutorial video:
https://www.youtube.com/watch?v=JRCJ6RtE3xU

"""

import smtplib
from email.message import EmailMessage

from flask_app import get_email_settings


def send_email(recipient_address: str, subject: str, rendered_template: str):
    email_settings = get_email_settings()

    message = EmailMessage()
    message['Subject'] = subject
    message['From'] = email_settings['email_address']
    message['To'] = recipient_address
    message.add_alternative(rendered_template, subtype="html")

    with smtplib.SMTP(email_settings['server'], email_settings['port']) as smtp:
        smtp.ehlo()
        smtp.starttls()  # Encrypt traffic.
        smtp.ehlo()
        smtp.login(email_settings['email_address'], email_settings['email_password'])

        smtp.send_message(message)
