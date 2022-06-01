from flask import session, abort, redirect, render_template, request, flash

from flask_app import app
from flask_app.models.event import Event
from flask_app.models.event_location import EventLocation
from flask_app.models.private_event import PrivateEvent


@app.route('/events/edit/<string:share_key>/')
def edit_event(share_key: str):
    if 'user_id' not in session:
        return redirect('/login/')

    found_event = Event.get_by_share_key(share_key)
    if found_event is None:
        abort(404)
    elif not found_event.can_be_edited():
        abort(403)

    form_data = found_event.to_dict()
    if found_event.get_event_location() is not None:
        form_data['checkbox_add_location_data'] = True
        location_dict = found_event.get_event_location().to_dict()
        for key in location_dict:
            form_data[key] = location_dict[key]
    if found_event.get_private_event() is not None:
        form_data['checkbox_add_private_event_key'] = True
        private_key_dict = found_event.get_private_event().to_dict()
        for key in private_key_dict:
            form_data[key] = private_key_dict[key]

    context = {
        'form_data': form_data,
        'on_edit_page': True,
    }

    if 'form_data' in session:
        context['form_data'] = session.pop('form_data')

    return render_template('edit_event.html', **context)


@app.route('/events/update/<string:share_key>/', methods=["POST", ])
def update_event(share_key: str):
    if 'user_id' not in session:
        return redirect('/login/')

    found_event = Event.get_by_share_key(share_key)
    if found_event is None:
        abort(404)
    elif not found_event.can_be_edited():
        abort(403)

    form_data = dict(request.form)
    cleaned_data = Event.clean_form_data(form_data)
    cleaned_data = EventLocation.clean_data(cleaned_data)
    cleaned_data['name'] = "Events cannot change their names."  # This is a placeholder to pass validation checks.
    cleaned_data['event_id'] = found_event.id

    # Validate inputs.
    form_data_is_valid = True
    if not Event.validate_new_event(cleaned_data):
        form_data_is_valid = False
    if 'checkbox_add_location_data' in cleaned_data and \
            not EventLocation.validate_new_event_location(cleaned_data, ignore_event_id_check=True):
        form_data_is_valid = False
    if 'checkbox_add_private_event_key' in cleaned_data and \
            not PrivateEvent.validate_new_private_event(cleaned_data, ignore_event_id_check=True):
        form_data_is_valid = False
    if not form_data_is_valid:
        session['form_data'] = form_data
        return redirect('/events/edit/{}/'.format(share_key))

    # TODO: Edit the event in the database.
    # Events cannot change their name, so do not modify that attribute.
    found_event.start_time = cleaned_data['start_time']
    found_event.end_time = cleaned_data['end_time']
    found_event.description = cleaned_data['description']
    found_event.update()

    found_event_location = found_event.get_event_location()
    if 'checkbox_add_location_data' in cleaned_data:  # Event location should exist.
        if found_event_location is None:
            EventLocation.create(cleaned_data)
        else:
            found_event_location.street = cleaned_data['street']
            found_event_location.city = cleaned_data['city']
            found_event_location.state = cleaned_data['state']
            found_event_location.country = cleaned_data['country']
            found_event_location.postal_code = cleaned_data['postal_code']
            found_event_location.notes = cleaned_data['notes']
            found_event_location.update()
    elif found_event_location is not None:  # Event location does exist and shouldn't.
        EventLocation.delete_by_event_id(found_event_location.event_id)

    found_private_event = found_event.get_private_event()
    if 'checkbox_add_private_event_key' in cleaned_data:  # Event private key should exist.
        if found_private_event is None:
            PrivateEvent.create(cleaned_data)
        else:
            found_private_event.secret_key = cleaned_data['secret_key']
            found_private_event.update()
    elif found_private_event is not None:  # Event private key does exist and shouldn't.
        PrivateEvent.delete_by_event_id(found_private_event.event_id)

    return redirect('/events/view/{}/'.format(share_key))


@app.route('/events/cancel/<string:share_key>/', methods=["POST", ])
def cancel_event(share_key: str):
    if 'user_id' not in session:
        return redirect('/login/')

    # Validate inputs.
    found_event = Event.get_by_share_key(share_key)
    form_data = dict(request.form)
    if 'name' not in form_data:
        flash("No value was set for the event's name.")
        session['form_data'] = form_data
        return redirect('/events/view/{}/'.format(share_key))
    elif form_data['name'].lower() != found_event.name.lower():
        flash("The provided name was not equal to the event's actual name.")
        session['form_data'] = form_data
        return redirect('/events/view/{}/'.format(share_key))
    if found_event is None:
        abort(404)
    elif found_event.get_author_user() is None:
        abort(403)

    # Cancel the event.
    if found_event.get_author_user().id == session['user_id']:
        found_event.canceled = True
        found_event.update()

    return redirect('/events/view/{}/'.format(share_key))


@app.route('/events/uncancel/<string:share_key>/')
def uncancel_event(share_key: str):
    if 'user_id' not in session:
        return redirect('/login/')

    found_event = Event.get_by_share_key(share_key)
    if found_event is None:
        abort(404)
    elif found_event.get_author_user().id == session['user_id']:
        found_event.canceled = False
        found_event.update()

    return redirect('/events/view/{}/'.format(share_key))




