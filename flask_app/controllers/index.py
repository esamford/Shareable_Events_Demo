from flask import render_template, redirect

from flask_app import app
from flask_app.models import event


@app.route('/')
def index():
    # The index page hasn't been finished yet. I still need to write up a sales pitch and maybe get some image assets
    # to put up on the page.
    redirect_to_login = False
    if redirect_to_login:
        return redirect('/login/')

    context = {
        'num_events': event.Event.get_record_count(),
    }
    return render_template('index.html', **context)


