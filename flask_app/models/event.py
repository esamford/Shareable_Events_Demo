import copy
import datetime
import secrets
from typing import Any

from flask import flash, session

from flask_app.controllers import event_comments
from flask_app.models import attendee, user_creates_event, event_location, private_event, user, user_is_attendee
from flask_app.utils.data_cleaning import remove_excessive_newlines
from flask_app.utils.database import get_database


class Event:
    def __init__(self, data: dict):
        self.id = data['id']
        self.created_at = data['created_at']
        self.updated_at = data['updated_at']
        self.name = data['name']
        self.share_key = data['share_key']
        self.start_time = data['start_time']
        self.end_time = data['end_time']
        self.description = data['description']
        self.canceled = data['canceled']

        self.__attendees = None
        self.__author_user = -1     # -1 instead of None because of possible None return type.
        self.__event_location = -1  # -1 instead of None because of possible None return type.
        self.__private_event = -1   # -1 instead of None because of possible None return type.
        self.__event_comments = None

    def get_attendees(self) -> list:
        if self.__attendees is None:
            self.__attendees = attendee.Attendee.get_by_event_id(self.id)
            self.__attendees.sort(key=lambda x: (x.first_name, x.last_name))
        return self.__attendees

    def get_author_user(self) -> Any or None:
        if self.__author_user == -1:
            uce_obj = user_creates_event.UserCreatesEvent.get_by_event_id(self.id)
            if uce_obj is None:
                self.__author_user = None
                return self.__author_user
            self.__author_user = user.User.get_by_id(uce_obj.user_id)
        return self.__author_user

    def get_event_location(self) -> Any or None:
        if self.__event_location == -1:
            self.__event_location = event_location.EventLocation.get_by_event_id(self.id)
        return self.__event_location

    def get_private_event(self) -> Any or None:
        if self.__private_event == -1:
            self.__private_event = private_event.PrivateEvent.get_by_event_id(self.id)
        return self.__private_event

    def get_event_comments(self) -> list:
        if self.__event_comments is None:
            self.__event_comments = event_comments.EventComment.get_by_event_id(self.id)
            self.__event_comments.sort(key=lambda x: x.created_at)
        return self.__event_comments

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'name': self.name,
            'share_key': self.share_key,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'description': self.description,
            'canceled': self.canceled,
        }

    def show_private_key(self) -> bool:
        if self.get_private_event() is None:
            return False
        elif 'user_id' not in session:
            return False
        elif self.get_author_user() is None:
            return False
        elif self.get_author_user().id != session['user_id']:
            return False
        else:
            return True

    def show_cancel_button(self) -> bool:
        if self.event_has_ended():
            return False
        elif 'user_id' not in session:
            return False
        elif self.get_author_user() is None:
            return False
        elif self.get_author_user().id != session['user_id']:
            return False
        else:
            return True

    def event_is_ongoing(self):
        event_started = bool(self.start_time <= datetime.datetime.utcnow())
        if event_started and not self.event_has_ended():
            return True
        else:
            return False

    def event_has_ended(self) -> bool:
        return self.end_time < datetime.datetime.utcnow()

    def can_be_edited(self) -> bool:
        if self.event_is_ongoing() or self.event_has_ended():
            return False
        elif 'user_id' not in session:
            return False
        elif self.get_author_user() is None:
            return False
        elif self.get_author_user().id != session['user_id']:
            return False
        else:
            return True

    def user_is_attending(self, user_id: int) -> bool:
        return bool(user_is_attendee.UserIsAttendee.get_by_user_id_and_event_id(user_id, self.id) is not None)

    @classmethod
    def clean_form_data(cls, data: dict) -> dict:
        """
        NOTE: It is very important NOT to clean the data twice. Otherwise, the start and end times will be converted to
        UTC time twice, then converted to client local time once. This will lead to the wrong time and confuse people.
        """
        data = copy.deepcopy(data)

        if 'name' in data:
            data['name'] = str(data['name']).title()
            data['name'] = data['name'].replace("'S", "'s")

        if 'timezone_offset' in data:
            data['timezone_offset'] = int(data['timezone_offset'])

        for time_key in ('start_time', 'end_time'):
            if time_key in data:
                new_time = data[time_key]
                if isinstance(new_time, str):
                    new_time = datetime.datetime.strptime(data[time_key], "%Y-%m-%dT%H:%M")  # Local time
                if 'timezone_offset' in data:
                    new_time = new_time + datetime.timedelta(minutes=data['timezone_offset'])  # Standardized time
                data[time_key] = new_time

        if 'description' in data:
            data['description'] = remove_excessive_newlines(data['description'])

        return data

    @classmethod
    def validate_new_event(cls, data: dict) -> bool:
        is_valid = True

        for key in ('name', 'start_time', 'end_time', 'description'):
            if key not in data:
                flash("The '{}' field was not provided.".format(key))
                is_valid = False
        if not is_valid:
            return is_valid

        if len(data['name']) < 2:
            flash("The provided name was less than two characters long.")
            is_valid = False
        if len(data['name']) > 50:
            flash("The provided name was greater than fifty characters long.")
            is_valid = False

        # Start and end times should already be in UTC format because of self.clean_data().
        if data['start_time'] < datetime.datetime.utcnow():
            flash("The provided start time is in the past.")
            is_valid = False
        if data['end_time'] < datetime.datetime.utcnow():
            flash("The provided end time is in the past.")
            is_valid = False

        if data['start_time'] >= data['end_time']:
            flash("The provided start time must be before the provided end time.")
            is_valid = False
        if len(data['description']) < 10:
            flash("The provided event description is shorter than ten characters.")
            is_valid = False
        if len(data['description']) > 1000:
            flash("The provided event description is longer than one-thousand characters.")
            is_valid = False

        return is_valid

    @classmethod
    def create(cls, data: dict) -> int:
        # Generate missing values.
        data['share_key'] = secrets.token_urlsafe(32)
        while cls.get_by_share_key(data['share_key']) is not None:
            data['share_key'] = secrets.token_urlsafe(32)
        data['canceled'] = data['canceled'] if 'canceled' in data else False

        db = get_database()
        return db.execute_insert(
            """
            INSERT INTO events (name, share_key, start_time, end_time, description, canceled)
            VALUES (
                %(name)s,
                %(share_key)s,
                %(start_time)s,
                %(end_time)s,
                %(description)s,
                %(canceled)s
            );
            """,
            data
        )

    @classmethod
    def get_by_id(cls, id: int, *args, **kwargs) -> Any or None:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM events WHERE id = %(id)s LIMIT 1;
            """,
            {'id': id, }
        )
        if len(items) > 0:
            return cls(items[0])
        else:
            return None

    @classmethod
    def get_by_share_key(cls, share_key: str, *args, **kwargs):
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM events WHERE share_key = %(share_key)s LIMIT 1;
            """,
            {'share_key': share_key, }
        )
        if len(items) > 0:
            return cls(items[0])
        else:
            return None

    @classmethod
    def get_by_author_id(cls, user_id: int, *args, **kwargs) -> list:
        user_creates_event_list = user_creates_event.UserCreatesEvent.get_by_user_id(user_id)
        result = []
        for uce in user_creates_event_list:
            assert isinstance(uce, user_creates_event.UserCreatesEvent)
            found_event = cls.get_by_id(uce.event_id)
            if found_event is not None:
                result.append(found_event)
        return result

    @classmethod
    def get_by_user_id_through_attendee(cls, user_id: int, *args, **kwargs) -> list:
        attendee_list = attendee.Attendee.get_by_user_id(user_id)

        result = []
        for a in attendee_list:
            assert isinstance(a, attendee.Attendee)
            found_event = cls.get_by_id(a.event_id)
            if found_event is not None:
                result.append(found_event)
        return result

    @classmethod
    def get_record_count(cls) -> int:
        db = get_database()
        items = db.execute_query(
            """
            SELECT COUNT(id) AS 'count' FROM events;
            """
        )
        return items[0]['count']

    def update(self):
        db = get_database()
        db.execute_query(
            """
            UPDATE events SET
                name = %(name)s,
                share_key = %(share_key)s,
                start_time = %(start_time)s,
                end_time = %(end_time)s,
                description = %(description)s,
                canceled = %(canceled)s
            WHERE
                id = %(id)s;
            """,
            self.to_dict()
        )

    @classmethod
    def delete_by_id(cls, id: int, *args, **kwargs):
        db = get_database()
        db.execute_query(
            """
            DELETE FROM events WHERE id = %(id)s;
            """,
            {'id': id, }
        )






