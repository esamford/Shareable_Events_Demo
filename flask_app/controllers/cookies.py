from flask import session, redirect, request, url_for, jsonify

from flask_app import app


@app.route('/accept_cookies/')
def accept_cookies():
    """
    This should be called asynchronously via JavaScript.
    Changes should take effect immediately server-side,
    but won't be noticed client-side until the next page is loaded.
    """
    session['accepted_cookies'] = True
    return jsonify(accepted_cookies=True)




