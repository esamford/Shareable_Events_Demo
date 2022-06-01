import datetime

from flask import render_template, request, session, redirect, flash

from flask_app import app, LOG_TYPE_EVENT_CREATION, SECURITY_SETTINGS
from flask_app.models.client_ip_address import ClientIPAddress
from flask_app.models.event import Event
from flask_app.models.event_location import EventLocation
from flask_app.models.private_event import PrivateEvent
from flask_app.models.security_log import SecurityLog
from flask_app.models.user import User
from flask_app.models.user_creates_event import UserCreatesEvent
from flask_app.utils.logging import log_security_issue
from flask_app.utils.utils_requests import get_client_ip


@app.route("/events/create/")
def create_event():
    context = {}
    if 'form_data' in session:
        context['form_data'] = session.pop('form_data')
    return render_template("create_event.html", **context)


@app.route('/events/create/', methods=["POST", ])
def create_new_event():
    form_data = dict(request.form)
    cleaned_data = Event.clean_form_data(form_data)

    # Check that the client isn't spamming the website with events.
    minutes_between_events = SECURITY_SETTINGS['event_created_timeout_min']
    client_ip = get_client_ip(request)
    client_ip_address = ClientIPAddress.get_by_ip_address(client_ip)
    if client_ip_address is not None:
        event_creation_logs = SecurityLog.get_by_client_ip_address_id_and_log_type_after_created_at(
            client_ip_address.id,
            LOG_TYPE_EVENT_CREATION,
            datetime.datetime.now() - datetime.timedelta(minutes=minutes_between_events)
        )
        if len(event_creation_logs) > 0:
            # Display a message and autocomplete form data.
            flash(
                "To reduce bot activity, each person is limited to creating one event per {} "
                "minutes. Please wait before trying again.".format(minutes_between_events)
            )
            session['form_data'] = form_data
            return redirect('/events/create/')

    # Validate user information, if the user is logged in.
    user_id = None
    if 'user_id' in session:
        user_id = session['user_id']
        if User.get_by_id(user_id) is None:
            flash("There was an error regarding your user account, and so you have been logged out. "
                  "If you would like to log in again, you can do so in another tab to prevent losing your "
                  "progress here. ")
            session.pop('user_id')  # Log the user out.
            session['form_data'] = form_data
            return redirect('/events/create/')

    # Validate the new event information.
    if not Event.validate_new_event(cleaned_data):
        session['form_data'] = form_data
        return redirect('/events/create/')

    # Validate the new event location information.
    if 'checkbox_add_location_data' in form_data:  # If the checkbox was checked, the dict should have a key.
        if not EventLocation.validate_new_event_location(cleaned_data, ignore_event_id_check=True):
            session['form_data'] = form_data
            return redirect('/events/create/')

    # Validate the new private event information.
    if 'checkbox_add_private_event_key' in form_data:  # If the checkbox was checked, the dict should have a key.
        if not PrivateEvent.validate_new_private_event(cleaned_data, ignore_event_id_check=True):
            session['form_data'] = form_data
            return redirect('/events/create/')

    # If everything is valid, create the records in the event tables.
    event_id = Event.create(cleaned_data)
    event = Event.get_by_id(event_id)
    cleaned_data['event_id'] = event_id
    if 'checkbox_add_location_data' in form_data:
        EventLocation.create(cleaned_data)
    if 'checkbox_add_private_event_key' in form_data:
        PrivateEvent.create(cleaned_data)

    # Log the event creation.
    log_security_issue(client_ip, LOG_TYPE_EVENT_CREATION)

    # If user_id is not None, link the created event with the user.
    if user_id is not None:
        cleaned_data['user_id'] = user_id
        UserCreatesEvent.create(cleaned_data)

    return redirect('/events/view/{}/'.format(event.share_key))




