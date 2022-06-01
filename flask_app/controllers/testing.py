from flask import abort, request, session, redirect, render_template

from flask_app import app, get_domain_address
from flask_app.models import user, verified_email


@app.route('/tests/abort_<int:error_code>/')
def call_abort(error_code: int):
    abort(error_code)


@app.route('/tests/get_client_time/')
def get_client_time():
    print(request.headers)
    abort(404)


@app.route('/tests/clear_session/')
def clear_session():
    session.clear()
    return redirect('/')


@app.route('/tests/print_session/')
def print_session():
    return str(dict(session))


@app.route('/tests/show_alert/')
def show_modal():
    session['alert'] = (
        "This is the title",
        (
            "This is the content that goes inside the body of the modal.",
            "This is the second paragraph in the body."
        )
    )
    return redirect('/')


@app.route('/tests/send_registration_email/<string:my_email>/')
def send_registration_email(my_email: str):
    found_user = user.User.get_by_email(my_email)
    if found_user is not None:
        verified_email.VerifiedEmail.send_verification_email_to_address(found_user.id, my_email)
    return redirect('/')


@app.route('/tests/show_registration_email/<string:my_email>/')
def show_registration_email(my_email: str):
    found_user = user.User.get_by_email(my_email)
    found_verification = verified_email.VerifiedEmail.get_by_user_id(found_user.id)
    context = {
        'first_name': found_user.first_name,
        'verification_url': "{}/verify_email/{}/{}/".format(
            get_domain_address().strip('/'), found_user.id, found_verification.verification_code
        ),
    }
    return render_template('/email_html/registration_email.html', **context)


@app.route('/tests/show_password_reset_email/<int:user_id>/')
def show_password_reset_email(user_id: int):
    found_user = user.User.get_by_id(user_id)
    context = {
        'first_name': found_user.first_name,
        'password_reset_url': "#",
        'domain': get_domain_address()
    }
    return render_template('/email_html/password_reset_email.html', **context)




