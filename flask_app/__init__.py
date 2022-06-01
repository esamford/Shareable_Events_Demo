import os
import re
import secrets

from flask import Flask
from flask_bcrypt import Bcrypt


def get_domain_address() -> str:
    if os.name == 'nt':  # Windows (local machine)
        return "http://127.0.0.1:5000"
    else:  # Not Windows (server)
        return "https://www.ShareableEvents.com"


app = Flask(__name__)
app.secret_key = "Secret key goes here."
bcrypt = Bcrypt(app)
BCRYPT_HASH_REGEX = re.compile(r"^\$[0-9]+[a-zA-Z]+\$[0-9]+\$[0-9a-zA-Z.\/]+$")


def get_db_connection_settings() -> dict:
    if os.name == 'nt':  # Windows (local machine)
        return {
            'db_name': "shareable_events_schema",
            'host': 'localhost',
            'user': 'root',
            'password': 'root',
        }
    else:  # Not Windows (server)
        return {
            'db_name': "shareable_events_schema",
            'host': 'localhost',
            'user': 'root',
            'password': "Server's MySQL database password goes here.",
        }


def get_email_settings() -> dict:
    return {
        'server': 'smtp.gmail.com',
        'port': 587,
        'email_address': 'Gmail address goes here.',
        'email_password': 'Gmail password goes here.',
    }


ip_hash_key = secrets.token_urlsafe(256).replace('$', '-')  # Used for hashing IP addresses kept for security reasons.


# Security settings and types for logging.
SECURITY_SETTINGS = {
    'event_created_timeout_min': 2,
    'failed_login_timeout_min': 15,
    'failed_attendee_login_timeout_min': 15,
    'failed_private_key_timeout_min': 15,
    'failed_event_url_guess': 30,
}
LOG_TYPE_EVENT_CREATION = "Event Creation Log"
LOG_TYPE_USER_LOGIN = "Failed User Login Log"
LOG_TYPE_ATTENDEE_LOGIN = "Failed Attendee Login Log"
LOG_TYPE_PRIVATE_EVENT_KEY = "Failed Private Event Secret Key"
LOG_TYPE_URL_GUESSING = "Entered Invalid Event URL"
