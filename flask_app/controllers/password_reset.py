"""
1. From the login page, click a link directing to a password reset page.
    This password reset page shows a form with an email address.
2. Submitting a registered user's email will tell the website to send a
    special URL to that address, if the address has been verified.
3. Clicking this URL from the email will send the user to a second page
    where they can set a new password and confirm this password.
4. Submitting this new password successfully will change the password
    in the database and redirect the user back to the login page.
"""


from flask import session, redirect, request, render_template, flash, abort, url_for

from flask_app import app
from flask_app.models import user, password_reset
from flask_app.models.exception import SiteException
from flask_app.utils.passwords import bcrypt_password_if_not


@app.route('/reset_password/request_reset/')
def request_password_reset():
    # The "reset_password" page should only be used by users who are not logged in.
    if 'user_id' in session:
        return redirect('/dashboard/')

    context = {}
    if 'form_data' in session:
        context['form_data'] = session.pop('form_data')

    return render_template('password_reset_request_email.html', **context)


@app.route('/reset_password/send_reset_email/', methods=["POST", ])
def process_form_password_reset_email():
    form_data = dict(request.form)

    # Verify that the email should be sent.
    found_user = user.User.get_by_email(**form_data)
    if found_user is None:
        flash("No user with that email exists in our records.")
        session['form_data'] = form_data
        return redirect('/reset_password/request_reset/')
    form_data['user_id'] = found_user.id
    if not password_reset.PasswordReset.validate_new_record(form_data):
        session['form_data'] = form_data
        return redirect('/reset_password/request_reset/')

    # Send the email.
    email_sent = password_reset.PasswordReset.send_password_reset_email_to_user(found_user.id)
    if email_sent:
        session['alert'] = (
            "Password Reset Email Sent",
            (
                "An email from ShareableEvents@gmail.com has been sent to your email address. "
                "Please follow the instructions within to reset your password.",
                "If you do not see the email in your inbox, check your spam folder."
            )
        )
    else:
        ex = Exception(
            "Could not send a password reset email to the user with an ID of '{}'. Check that you aren't being "
            "limited by Gmail.".format(found_user.id)
        )
        SiteException.create_by_exception(ex)
        session['alert'] = (
            "Error",
            (
                "We received your password reset request, but could not send your reset email. "
                "Please try again later."
            )
        )

    return redirect('/')


@app.route('/reset_password/<int:user_id>/<string:reset_code>/')
def show_password_reset_form(user_id: int, reset_code: str):
    if 'user_id' in session:
        session.pop('user_id')

    validate_data = {
        'user_id': user_id,
        'reset_code': reset_code,
    }
    if not password_reset.PasswordReset.validate_show_reset_password_form(validate_data):
        abort(403)

    context = {
        'user_id': user_id,
        'reset_code': reset_code,
    }
    return render_template('password_reset_change_password.html', **context)


@app.route('/reset_password/process_reset/', methods=["POST", ])
def process_form_password_reset():
    form_data = dict(request.form)

    if not password_reset.PasswordReset.validate_password_reset(form_data):
        return redirect(request.referrer or url_for('/'))

    found_user = user.User.get_by_id(int(form_data['user_id']))
    found_user.password = form_data['password']
    found_user.update()  # Password is hashed inside update.

    found_password_reset = password_reset.PasswordReset.get_by_user_id_and_reset_code(**form_data)
    found_password_reset.success = True
    found_password_reset.update()

    if 'user_id' in session:
        session.pop('user_id')

    session['alert'] = (
        "Your Password Has Been Reset",
        (
            "The password you just provided has been set as your current password. "
            "You can now log in again and continue using the site.",
        )
    )

    return redirect('/login/')

