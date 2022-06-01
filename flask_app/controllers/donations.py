from flask import session, redirect

from flask_app import app


@app.route('/donations/paypal/')
def show_donation_gratitude():
    session['alert'] = (
        'Thank You!',
        (
            "Thank you so much for your donation! Your support will help Shareable Events continue to operate.",
        )
    )
    return redirect('/')


