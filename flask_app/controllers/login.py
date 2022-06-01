import datetime

from flask import render_template, session, redirect, request, flash

from flask_app import app, SECURITY_SETTINGS, LOG_TYPE_USER_LOGIN
from flask_app.models.client_ip_address import ClientIPAddress
from flask_app.models.security_log import SecurityLog
from flask_app.models.user import User
from flask_app.utils.logging import log_security_issue
from flask_app.utils.utils_requests import get_client_ip


@app.route('/login/')
def login():
    if 'user_id' in session:
        return redirect('/dashboard/')

    context = {}
    if 'form_data' in session:
        context['form_data'] = session.pop('form_data')
    return render_template('login.html', **context)


@app.route('/login/process_form/', methods=["POST", ])
def process_login():
    form_data = dict(request.form)

    # Check for too many failed login attempts from this client within the last few minutes.
    # If suspicious activity is detected, do not continue with the login process.
    timeout_minutes = SECURITY_SETTINGS['failed_login_timeout_min']
    client_ip = get_client_ip(request)
    client_ip_address = ClientIPAddress.get_by_ip_address(client_ip)
    if client_ip_address is not None:
        user_login_logs = SecurityLog.get_by_client_ip_address_id_and_log_type_after_created_at(
            client_ip_address.id,
            LOG_TYPE_USER_LOGIN,
            datetime.datetime.now() - datetime.timedelta(minutes=timeout_minutes)
        )
        if len(user_login_logs) >= 2:  # Block client on third failed attempt.
            log_security_issue(client_ip, LOG_TYPE_USER_LOGIN)

            # Display a message and autocomplete form data.
            flash(
                "You have failed to login as too many times. "
                "For security purposes, please wait {} minutes before trying again.".format(timeout_minutes)
            )
            session['form_data'] = form_data
            return redirect('/login/')

    # If the login information is invalid, log a failed login attempt and ask them to try again.
    if not User.validate_login(form_data):
        log_security_issue(client_ip, LOG_TYPE_USER_LOGIN)
        session['form_data'] = form_data
        return redirect('/login/')

    user = User.get_by_email_and_password(**form_data)
    assert user is not None
    session['user_id'] = user.id

    return redirect('/dashboard/')


@app.route('/logout/')
def logout():
    if 'user_id' in session:
        session.pop('user_id')
    return redirect('/')
