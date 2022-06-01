# NOTE: This script should be run from inside the Shareable_Events_Demo project folder.
cd /home/ubuntu/Shareable_Events

# Initial server setup.
sudo apt-get update
sudo apt-get install python3-pip nginx gunicorn git mysql-server -y
sudo apt-get update

# Make sure everything is installed before importing Python modules.
# Otherwise, flask-bcrypt will fail to install.
sudo apt-get install gcc libpq-dev -y
sudo apt-get install python-dev  python-pip -y
sudo apt-get install python3-dev python3-pip python3-venv python3-wheel -y

# Import all requirements for the Flask application.
python3 -m venv venv
source venv/bin/activate
pip3 install wheel
pip3 install -r requirements.txt
pip3 install gunicorn==20.0.2
# gunicorn --bind 0.0.0.0:5000 wsgi:application
deactivate
