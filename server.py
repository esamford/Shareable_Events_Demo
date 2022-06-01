from flask_app import app
from flask_app.controllers import \
    exception_handling, cookies, themes, index, register, verify_email, login, \
    account_settings, dashboard, create_events, view_events, edit_events, event_comments, \
    attendees, password_reset, server_files, donations
# from flask_app.controllers import testing


def remember_imports():
    # _ = testing.app  # TODO: Remove after testing.

    _ = exception_handling.app
    _ = cookies.app
    _ = themes.app
    _ = index.app
    _ = register.app
    _ = verify_email
    _ = login.app
    _ = account_settings.app
    _ = dashboard.app
    _ = create_events.app
    _ = view_events.app
    _ = edit_events.app
    _ = event_comments.app
    _ = attendees.app
    _ = password_reset.app
    _ = server_files.app
    _ = donations.app


def clean_database():
    verify_email.VerifiedEmail.delete_expired_users()  # Delete users who never verified their email.


if __name__ == "__main__":
    clean_database()
    app.run(debug=True)


