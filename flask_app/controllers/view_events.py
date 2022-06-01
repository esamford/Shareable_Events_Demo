import datetime
import os

from flask import request, session, render_template, abort, flash, url_for

from flask_app import app, SECURITY_SETTINGS, LOG_TYPE_PRIVATE_EVENT_KEY, get_domain_address, LOG_TYPE_URL_GUESSING
from flask_app.models.client_ip_address import ClientIPAddress
from flask_app.models.event import Event
from flask_app.models.private_event import PrivateEvent
from flask_app.models.security_log import SecurityLog
from flask_app.models.user import User
from flask_app.utils.ad_utils import get_ad_paths
from flask_app.utils.logging import log_security_issue
from flask_app.utils.utils_requests import get_client_ip


@app.route('/events/view/<string:share_key>/')
def view_event(share_key: str):
    request_arg_dict = dict(request.args)  # Get ? parameters from the URL.

    # Prevent URL guessing by the client.
    timeout_minutes = SECURITY_SETTINGS['failed_event_url_guess']
    client_ip = get_client_ip(request)
    client_ip_address = ClientIPAddress.get_by_ip_address(client_ip)
    if client_ip_address is not None:
        url_guesses = SecurityLog.get_by_client_ip_address_id_and_log_type_after_created_at(
            client_ip_address.id,
            LOG_TYPE_URL_GUESSING,
            datetime.datetime.now() - datetime.timedelta(minutes=timeout_minutes)
        )
        if len(url_guesses) >= 4:  # Block client on fifth failed attempt.
            log_security_issue(client_ip, LOG_TYPE_URL_GUESSING)

            session['alert'] = (
                "URL Guessing Detected",
                (
                    "It seems as though you are trying to guess an event URL. To protect our users from "
                    "malicious activity, access to events will be blocked for the next {} "
                    "minutes.".format(timeout_minutes),
                    "If you are a real user having trouble accessing an event, please take this time to "
                    "double-check that the URL you are using is correct."
                )
            )
            abort(403)

    # Check that the event exists. If not, log a URL guess attempt and show a 404 page.
    found_event = Event.get_by_share_key(share_key)
    if found_event is None:
        log_security_issue(get_client_ip(request), LOG_TYPE_URL_GUESSING)
        abort(404)

    # Set default context.
    context = {
        'event': found_event,
        'passed_secret_key_check': False,
        'user_created_event': False,
        'shorten_attendees': False,  # Also found on the dashboard page.
        'event_url': '{}/events/view/{}/'.format(get_domain_address().strip('/'), share_key),
        'active_tab': 0,  # Default to event info.
    }

    # Add context so that the attendee signup section knows what to show.
    if 'user_id' in session:
        context['logged_in_user'] = User.get_by_id(session['user_id'])

    # Choose which tab to default to.
    if 'form_data' in session:
        form_data = session.pop('form_data')
        context['form_data'] = form_data
        if 'form_name' in form_data and form_data['form_name'] == "add_comment":
            context['active_tab'] = 1  # Switch default tab to "Comments".
        elif 'form_name' in form_data and form_data['form_name'] == "cancel_event":
            context['active_tab'] = 2  # Switch default tab to "Other".

    # If this user was the one who created the event, don't require a password.
    # Also, flag that this user is the one who created the event.
    if 'user_id' in session:
        author_user = found_event.get_author_user()
        if author_user is not None and author_user.id == session['user_id']:
            context['passed_secret_key_check'] = True
            context['user_created_event'] = True

    # Prevent secret key guessing.
    # Do this after checking if the logged in user is the creator, since they do not need to pass their own checks.
    # Do this before checking everyone else, since they should not be allowed to continue guessing.
    if found_event.get_private_event() is not None and not context['user_created_event']:
        timeout_minutes = SECURITY_SETTINGS['failed_private_key_timeout_min']
        client_ip = get_client_ip(request)
        client_ip_address = ClientIPAddress.get_by_ip_address(client_ip)
        if client_ip_address is not None:
            failed_attendee_logins = SecurityLog.get_by_client_ip_address_id_and_log_type_after_created_at(
                client_ip_address.id,
                LOG_TYPE_PRIVATE_EVENT_KEY,
                datetime.datetime.now() - datetime.timedelta(minutes=timeout_minutes)
            )
            if len(failed_attendee_logins) >= 2:  # Block client on third failed attempt.
                log_security_issue(client_ip, LOG_TYPE_PRIVATE_EVENT_KEY)

                # Display a message and autocomplete form data.
                flash(
                    "You have guessed an event's secret key too many times. "
                    "Please wait {} minutes before trying again.".format(timeout_minutes)
                )
                context['passed_secret_key_check'] = False
                render_template('view_event.html', **context)

    # Check to see if the page should show a password request form instead.
    if not context['passed_secret_key_check']:
        if found_event.get_private_event() is None:
            context['passed_secret_key_check'] = True
        elif 'secret_key' in request_arg_dict:
            context['passed_secret_key_check'] = \
                PrivateEvent.validate_access_with_event_id_and_secret_key(
                    found_event.id, request_arg_dict['secret_key']
                )
            if not context['passed_secret_key_check']:
                client_ip = get_client_ip(request)
                log_security_issue(client_ip, LOG_TYPE_PRIVATE_EVENT_KEY)

    # Put advertisements on the page. TODO
    if context['passed_secret_key_check'] and not found_event.canceled:
        # context['advertisements'] = get_ad_paths(2)
        pass

    return render_template('view_event.html', **context)


