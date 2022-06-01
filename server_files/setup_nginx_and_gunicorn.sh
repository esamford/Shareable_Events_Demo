cd /home/ubuntu/Shareable_Events

# Copy Gunicorn's "gunicorn.service" file to the expected directory, then enable it.
sudo rm /etc/systemd/system/gunicorn.service
sudo cp -fr server_files/gunicorn.service /etc/systemd/system/gunicorn.service

# Configure Nginx.
sudo rm /etc/nginx/sites-enabled/flask_app
sudo rm /etc/nginx/sites-available/flask_app
sudo cp -fr server_files/flask_app /etc/nginx/sites-available/flask_app
sudo ln -s /etc/nginx/sites-available/flask_app /etc/nginx/sites-enabled
sudo rm /etc/nginx/sites-enabled/default
sudo rm /etc/nginx/sites-available/default

sudo systemctl daemon-reload
