from flask import render_template, request, redirect, session

from flask_app import app
from flask_app.models.user import User


@app.route('/register/')
def register():
    context = {}
    if 'form_data' in session:
        context['form_data'] = session.pop('form_data')

    if 'user_id' in session:
        return redirect('/dashboard/')

    return render_template('register.html', **context)


@app.route('/register/new/', methods=["POST", ])
def register_new_user():
    # Users shouldn't be creating new accounts while logged in.
    if 'user_id' in session:
        return redirect('/dashboard/')

    form_data = dict(request.form)

    if not User.validate_new_user(form_data):
        session['form_data'] = form_data
        return redirect('/register/')

    # Create the user and assign 'user_id' to the session.
    user_id = User.create(form_data)
    session['user_id'] = user_id

    session['alert'] = (
        "Verify Your Email",
        (
            "A verification email from ShareableEvents@gmail.com has been sent to your email address. "
            "If you do not see it in your inbox, check your spam folder.",
        )
    )
    return redirect('/dashboard/')





