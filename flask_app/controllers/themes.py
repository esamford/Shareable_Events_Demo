from flask import session, redirect, request, url_for

from flask_app import app


@app.route('/themes/dark/')
def enable_dark_theme():
    session['dark_theme'] = True
    return redirect(request.referrer or url_for('/'))


@app.route('/themes/light/')
def enable_light_theme():
    if 'dark_theme' in session:
        session.pop('dark_theme')
    return redirect(request.referrer or url_for('/'))



