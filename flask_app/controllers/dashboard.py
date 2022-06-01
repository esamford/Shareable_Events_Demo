import datetime

from flask import session, redirect, render_template, request, flash

from flask_app import app
from flask_app.models import user, event


@app.route('/dashboard/', methods=["GET", ])
def dashboard():
    if 'user_id' not in session:
        return redirect('/login/')
    if user.User.get_by_id(session['user_id']) is None:
        session.pop('user_id')
        return redirect('/login/')

    context = {
        'events': None,
        'show_view_button': True,
        'shorten_attendees': True,  # Also found on the "view event" page.
    }

    found_user = user.User.get_by_id(session['user_id'])
    if found_user is None:
        return redirect('/login/')
    context['user'] = found_user

    # Get all events.
    all_user_events = {
        'created_events': found_user.get_created_events(),
        'attending_events': found_user.get_attending_events(),
    }

    for event_type_key in all_user_events:
        found_events = all_user_events[event_type_key]

        # Check for form data (inside URL arguments). If it exists,
        # filter out events that don't match those requirements.
        show_default_events = True
        event_limit = 25
        form_data = dict(request.args)
        if len(form_data) > 0:
            context['form_data'] = form_data
            event_limit = int(form_data['max_num_results']) if 'max_num_results' in form_data else 25
            event_limit = min(50, max(1, event_limit))

            # Make sure that all inputs are accessible.
            form_data_is_valid = True
            for key in ('timezone_offset', 'min_start_time', 'max_start_time'):
                if key not in form_data:
                    flash("The following input was not provided: '{}'".format(key))
                    form_data_is_valid = False

            # Add the timezone offset and keep events that satisfy search filters.
            if form_data_is_valid:
                timezone_offset = int(form_data['timezone_offset'])
                min_start_utc = datetime.datetime.strptime(form_data['min_start_time'], "%Y-%m-%dT%H:%M") +\
                    datetime.timedelta(minutes=timezone_offset)
                max_start_utc = datetime.datetime.strptime(form_data['max_start_time'], "%Y-%m-%dT%H:%M") +\
                    datetime.timedelta(minutes=timezone_offset)

                if min_start_utc > max_start_utc:
                    flash("The minimum start time must be before the maximum start time.")
                else:
                    for x in range(len(found_events) - 1, -1, -1):
                        fe = found_events[x]
                        assert isinstance(fe, event.Event)
                        if not bool(min_start_utc <= fe.start_time <= max_start_utc):
                            found_events.pop(x)
                    show_default_events = False

        if show_default_events:
            for x in range(len(found_events) - 1, -1, -1):
                if found_events[x].event_has_ended():
                    found_events.pop(x)

        found_events.sort(key=lambda e: e.start_time)
        if len(found_events) > 0:
            context[event_type_key] = found_events[:event_limit]

    return render_template('dashboard.html', **context)

