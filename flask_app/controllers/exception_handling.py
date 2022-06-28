from flask import render_template
from werkzeug.exceptions import HTTPException

from flask_app import app
from flask_app.models.exception import SiteException


@app.errorhandler(Exception)
def handle_any_exception(e: Exception):
    print("Caught exception: {}".format(e))
    # raise e  # TODO: Remove after testing.
    SiteException.create(type=str(type(e)), message=str(e))

    # Not a 500-type exception; explain what went wrong so the user knows how to fix the problem.
    if isinstance(e, HTTPException):
        context = {
            'error_num': e.code,
            'message': e.description,
        }
    # 500-type exception; leave information ambiguous.
    else:
        context = {
            'error_num': 500,
            'message': "The server encountered an internal error and was unable to complete your request. "
                       "Either the server is overloaded or there is an error in the application."
        }
    return render_template('exception_page.html', **context), context['error_num']
