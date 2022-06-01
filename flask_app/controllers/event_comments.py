from flask import session, redirect, abort, request

from flask_app import app
from flask_app.models import event
from flask_app.models.event_comment import EventComment


@app.route('/event_comments/post/<string:share_key>/', methods=["POST", ])
def post_event_comment(share_key: str):
    if 'user_id' not in session:
        return redirect('/login/')

    found_event = event.Event.get_by_share_key(share_key)
    if found_event is None:
        abort(404)

    form_data = dict(request.form)
    form_data['user_id'] = session['user_id']
    form_data['event_id'] = found_event.id
    if not EventComment.validate_new_comment(form_data):
        session['form_data'] = form_data
        return redirect('/events/view/{}/'.format(share_key))

    EventComment.create(form_data)

    session['form_data'] = {'form_name': 'add_comment', }  # Default to "Comments" tab.

    return redirect(request.referrer)


@app.route('/event_comments/delete/<int:comment_id>/')
def delete_event_comment(comment_id: int):
    if 'user_id' not in session:
        return redirect('/login/')

    found_comment = EventComment.get_by_id(comment_id)
    if found_comment is None:
        abort(404)
    elif found_comment.get_user().id != session['user_id']:
        abort(403)

    EventComment.delete_by_id(found_comment.id)

    session['form_data'] = {'form_name': 'add_comment', }  # Default to "Comments" tab.
    return redirect(request.referrer)




