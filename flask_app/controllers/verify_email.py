from flask import abort, redirect, session

from flask_app import app
from flask_app.models.user import User
from flask_app.models.verified_email import VerifiedEmail


@app.route('/verify_email/<int:user_id>/<string:verification_code>/')
def email_verified(user_id: int, verification_code: str):
    found_user = User.get_by_id(user_id)
    if found_user is None:
        abort(403)

    found_verified_email = VerifiedEmail.get_by_user_id(user_id)
    if found_verified_email is None:
        raise Exception("User did not have an email sent to them after registration.")

    if found_verified_email.verification_code != verification_code:
        abort(403)

    found_user.email = found_verified_email.new_email
    found_user.update()

    found_verified_email.verified = True
    found_verified_email.update()

    session['alert'] = (
        "Email Verification",
        (
            "Congrats, your email has been verified!",
        )
    )
    return redirect('/')









