# Gunicorn requires a Flask object called "application".
from server import app as application


if __name__ == "__main__":
    application.run()
