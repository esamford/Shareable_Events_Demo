import datetime

from flask import session, redirect, request, flash, abort

from flask_app import app, SECURITY_SETTINGS, LOG_TYPE_ATTENDEE_LOGIN
from flask_app.models import user, event
from flask_app.models.attendee import Attendee
from flask_app.models.client_ip_address import ClientIPAddress
from flask_app.models.security_log import SecurityLog
from flask_app.models.user_is_attendee import UserIsAttendee
from flask_app.utils.logging import log_security_issue
from flask_app.utils.utils_requests import get_client_ip


def redirect_back_to_attendee_signup():
    return redirect(str(request.referrer) + "#attendee_signup")


@app.route('/attendance/users/<string:share_key>/', methods=["POST", ])
def attend_event_user(share_key: str):
    # Validate inputs and redirect back if something is wrong.
    form_data = dict(request.form)
    found_event = event.Event.get_by_share_key(share_key)
    redirect_back = False
    if 'user_id' not in session:
        redirect_back = True
    elif 'attend_event' not in form_data:
        redirect_back = True
    elif form_data['attend_event'].lower() not in ("true", "false"):
        redirect_back = True
    elif found_event is None:
        redirect_back = True
    if redirect_back:
        # Don't use the secret key in case the URL was guessed.
        return redirect_back_to_attendee_signup()

    # Set the user attendee status.
    found_user = user.User.get_by_id(session['user_id'])
    if form_data['attend_event'] == "true" and not found_user.is_attending_event_with_id(found_event.id):
        new_attendee_id = Attendee.create_from_user_id_and_event_id(found_user.id, found_event.id)
        uia_data = {'user_id': found_user.id, 'attendee_id': new_attendee_id}
        if not UserIsAttendee.validate_new_user_is_attendee(uia_data):
            raise Exception(
                "Could not validate new user_is_attendee based on attendee and user info. "
                "User id = {}, attendee id = {}".format(found_user.id, new_attendee_id)
            )
        UserIsAttendee.create(uia_data)
    elif form_data['attend_event'] == "false" and found_user.is_attending_event_with_id(found_event.id):
        uia = UserIsAttendee.get_by_user_id_and_event_id(found_user.id, found_event.id)
        Attendee.delete_by_id(uia.get_attendee().id)
        UserIsAttendee.delete_by_user_id_and_attendee_id(uia.user_id, uia.attendee_id)

    return redirect_back_to_attendee_signup()


@app.route('/attendance/unknown_user/<string:share_key>/', methods=["POST", ])
def attend_event_unknown_user(share_key: str):
    # Validate inputs and redirect back if something is wrong.
    form_data = dict(request.form)
    found_event = event.Event.get_by_share_key(share_key)
    redirect_back = False
    if 'user_id' in session:
        redirect_back = True
    elif 'attend_event' not in form_data:
        redirect_back = True
    elif form_data['attend_event'].lower() not in ("true", "false"):
        redirect_back = True
    elif found_event is None:
        redirect_back = True
    if redirect_back:
        # Don't use the secret key in case the URL was guessed.
        return redirect_back_to_attendee_signup()

    # Prevent password guessing.
    timeout_minutes = SECURITY_SETTINGS['failed_attendee_login_timeout_min']
    client_ip = get_client_ip(request)
    client_ip_address = ClientIPAddress.get_by_ip_address(client_ip)
    if client_ip_address is not None:
        failed_attendee_logins = SecurityLog.get_by_client_ip_address_id_and_log_type_after_created_at(
            client_ip_address.id,
            LOG_TYPE_ATTENDEE_LOGIN,
            datetime.datetime.now() - datetime.timedelta(minutes=timeout_minutes)
        )
        if len(failed_attendee_logins) >= 2:  # Block client on third failed attempt.
            log_security_issue(client_ip, LOG_TYPE_ATTENDEE_LOGIN)

            # Display a message and autocomplete form data.
            flash(
                "You have failed to login as an attendee too many times. "
                "Please wait {} minutes before trying again.".format(timeout_minutes)
            )
            session['form_data'] = form_data
            return redirect_back_to_attendee_signup()

    # Set the non-registered user's attendee status.
    form_data['event_id'] = found_event.id
    if form_data['attend_event'] == "true":
        found_attendees = Attendee.get_by_full_name_and_event_id(**form_data)  # Ignore password for now.
        if len(found_attendees) > 0:
            flash(
                "An attendee with that first and last name is already signed up for this event. "
            )
            session['form_data'] = form_data
            return redirect_back_to_attendee_signup()
        if not Attendee.validate_new_attendee(form_data):
            session['form_data'] = form_data
            return redirect_back_to_attendee_signup()
        Attendee.create(form_data)
    elif form_data['attend_event'] == "false":
        # Make sure there is a non-registered user to remove from the attendee list.
        found_nonregistered_attendee = False
        found_registered_user = False
        for attendee in Attendee.get_by_full_name_and_event_id(**form_data):
            if attendee.get_user_if_exists() is None:
                found_nonregistered_attendee = True
            else:
                found_registered_user = True
        if not found_nonregistered_attendee and found_registered_user:
            flash("Registered users cannot be removed without first logging in.")
            session['form_data'] = form_data
            return redirect_back_to_attendee_signup()
        elif not found_nonregistered_attendee and not found_registered_user:
            flash("No attendees for this event have the provided first and last name.")
            session['form_data'] = form_data
            return redirect_back_to_attendee_signup()

        found_attendee = Attendee.get_by_all(**form_data)
        if not Attendee.validate_attendee_login(form_data):
            log_security_issue(client_ip, LOG_TYPE_ATTENDEE_LOGIN)

            # Redirect back.
            session['form_data'] = form_data
            return redirect_back_to_attendee_signup()
        if found_attendee.get_user_if_exists() is not None:
            flash("That attendee cannot be removed without first logging in.")
            session['form_data'] = form_data
            return redirect_back_to_attendee_signup()

        Attendee.delete_by_id(found_attendee.id)

    return redirect_back_to_attendee_signup()


@app.route('/attendance/remove_attendee/<string:share_key>/<int:attendee_id>/')
def author_removes_attendee(share_key: str, attendee_id: int):
    if 'user_id' not in session:
        return redirect('/login/')

    found_event = event.Event.get_by_share_key(share_key)
    if found_event is None:
        abort(404)
    elif found_event.get_author_user() is None:
        abort(403)
    elif found_event.get_author_user().id != session['user_id']:
        abort(403)

    found_attendee = Attendee.get_by_id(attendee_id)
    if found_attendee is None:
        return redirect(request.referrer)
    if found_attendee.get_event().id != found_event.id:
        return redirect(request.referrer)

    Attendee.delete_by_id(found_attendee.id)

    return redirect("/events/view/{}/".format(share_key))





