import copy
from typing import Any

from flask import flash

from flask_app.models import event
from flask_app.utils.data_cleaning import remove_excessive_newlines
from flask_app.utils.database import get_database


class EventLocation:
    def __init__(self, data: dict):
        self.event_id = data['event_id']
        self.created_at = data['created_at']
        self.updated_at = data['updated_at']
        self.street = data['street']
        self.city = data['city']
        self.state = data['state']
        self.country = data['country']
        self.postal_code = data['postal_code']
        self.notes = data['notes']

        self.__event = None

    def get_event(self):
        if self.__event is None:
            self.__event = event.Event.get_by_id(self.event_id)
        return self.__event

    def to_dict(self) -> dict:
        return {
            'event_id': self.event_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'street': self.street,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'postal_code': self.postal_code,
            'notes': self.notes,
        }

    def display_notes(self) -> bool:
        if len(self.notes) > 0 and not str(self.notes).isspace():
            return True
        else:
            return False

    @classmethod
    def clean_data(cls, data: dict) -> dict:
        data = copy.deepcopy(data)

        # TODO
        if 'street' in data:
            data['street'] = str(data['street']).title()
            data['street'] = data['street'].replace("'S", "'s")

        if 'city' in data:
            data['city'] = str(data['city']).title()
            data['city'] = data['city'].replace("'S", "'s")

        if 'state' in data:
            if len(data['state']) > 2:
                data['state'] = str(data['state']).title()
                data['state'] = data['state'].replace("'S", "'s")
            else:
                data['state'] = str(data['state']).upper()

        if 'country' in data:
            data['country'] = str(data['country']).title()
            data['country'] = data['country'].replace("'S", "'s")

        if 'notes' in data:
            data['notes'] = remove_excessive_newlines(data['notes'])

        return data

    @classmethod
    def validate_new_event_location(cls, data: dict, ignore_event_id_check: bool = False) -> bool:
        is_valid = True

        for key in ('street', 'city', 'country', 'postal_code', 'notes'):
            if key not in data:
                flash("The '{}' field was not provided.".format(key))
                is_valid = False
        if not is_valid:
            return is_valid

        if not ignore_event_id_check:
            if 'event_id' not in data:
                flash("The 'event_id' field was not provided.")
                is_valid = False
                return is_valid
            if event.Event.get_by_id(data['event_id']) is None:
                flash("The provided event ID cannot be found.")
                is_valid = False
        if len(data['street']) < 5:
            flash("The provided street was less than five characters long.")
            is_valid = False
        if len(data['street']) > 200:
            flash("The provided street was greater than two hundred characters long.")
            is_valid = False
        if len(data['city']) < 3:
            flash("The provided city was less than three characters long.")
            is_valid = False
        if len(data['city']) > 100:
            flash("The provided city was greater than one hundred characters long.")
            is_valid = False
        if len(data['state']) < 2:
            flash("The provided state was less than two characters long.")
            is_valid = False
        if len(data['state']) > 200:
            flash("The provided state was greater than two hundred characters long.")
            is_valid = False
        if len(data['country']) < 5:
            flash("The provided country was less than five characters long.")
            is_valid = False
        if len(data['country']) > 200:
            flash("The provided country was greater than two hundred characters long.")
            is_valid = False
        if len(data['postal_code']) < 5:
            flash("The provided postal code was less than seven characters long.")
            is_valid = False
        if len(data['postal_code']) > 20:
            flash("The provided postal code was greater than twenty characters long.")
            is_valid = False
        if len(data['notes']) > 1000:
            flash("The provided location notes were greater than one thousand characters long.")
            is_valid = False

        return is_valid

    @classmethod
    def create(cls, data: dict) -> int:
        if event.Event.get_by_id(data['event_id']) is None:
            raise Exception("The event does not exist.")

        data = cls.clean_data(data)

        db = get_database()
        return db.execute_insert(
            """
            INSERT INTO event_locations (event_id, street, city, state, country, postal_code, notes)
            VALUES (
                %(event_id)s,
                %(street)s,
                %(city)s,
                %(state)s,
                %(country)s,
                %(postal_code)s,
                %(notes)s
            );
            """,
            data
        )

    @classmethod
    def get_by_event_id(cls, event_id: int, *args, **kwargs) -> Any or None:
        db = get_database()
        items = db.execute_query(
            """
            SELECT * FROM event_locations WHERE event_id = %(event_id)s LIMIT 1;
            """,
            {'event_id': event_id, }
        )
        if len(items) > 0:
            return cls(items[0])
        else:
            return None

    def update(self):
        db = get_database()
        db.execute_query(
            """
            UPDATE event_locations SET
                street = %(street)s,
                city = %(city)s,
                state = %(state)s,
                country = %(country)s,
                postal_code = %(postal_code)s,
                notes = %(notes)s
            WHERE
                event_id = %(event_id)s;
            """,
            self.to_dict()
        )

    @classmethod
    def delete_by_event_id(cls, event_id: int, *args, **kwargs):
        db = get_database()
        db.execute_query(
            """
            DELETE FROM event_locations WHERE event_id = %(event_id)s;
            """,
            {'event_id': event_id, }
        )


