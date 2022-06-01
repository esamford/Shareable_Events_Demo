from flask import session, redirect, render_template, request

from flask_app import app
from flask_app.models.user import User
from flask_app.models.verified_email import VerifiedEmail


@app.route('/account_settings/')
def account_settings():
    if 'user_id' not in session:
        return redirect('/login/')

    context = {}
    if 'form_data' in session:
        context['form_data'] = session.pop('form_date')
    return render_template('account_settings.html', **context)


@app.route('/account_settings/change_password/', methods=["POST", ])
def change_user_password():
    if 'user_id' not in session:
        return redirect('/login/')

    found_user = User.get_by_id(session['user_id'])
    if found_user is None:
        session.pop('user_id')
        return redirect('/')

    form_data = dict(request.form)
    form_data['user_id'] = session['user_id']
    if not User.validate_password_change(form_data):
        session['form_data'] = form_data
        return redirect('/account_settings/')

    found_user.password = form_data['new_password']
    found_user.update()  # Passwords are hashed automatically if they aren't already.

    return redirect('/account_settings/')


@app.route('/account_settings/change_email/', methods=["POST", ])
def change_user_email():
    if 'user_id' not in session:
        return redirect('/login/')

    found_user = User.get_by_id(session['user_id'])
    if found_user is None:
        session.pop('user_id')
        return redirect('/')

    form_data = dict(request.form)
    form_data['user_id'] = session['user_id']
    if not VerifiedEmail.validate_email_change(form_data):
        session['form_data'] = form_data
        return redirect('/account_settings/')

    VerifiedEmail.send_verification_to_changed_email(**form_data)
    if VerifiedEmail.get_by_user_id(found_user.id).email_sent:
        session['alert'] = (
            "Verify New Email Address",
            (
                "An email has been sent to the specified address. "
                "Please verify your new email by clicking the provided link inside.",
            )
        )
    return redirect('/account_settings/')

