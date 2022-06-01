cd /home/ubuntu
clear

# Shut down existing Gunicorn versions and restart it.
# Doing this also re-creates the .sock file in the repository folder.
# If the .sock file doesn't exist, something may be wrong with the "gunicorn.server" file.
# If, Nginx is showing a 502 (bad gateway) error on the web, check that Gunicorn is running properly.
# These used to be just "gunicorn" instead of "gunicorn.service."
sudo systemctl stop gunicorn.service
sudo systemctl start gunicorn.service
sudo systemctl enable gunicorn.service
sudo systemctl status gunicorn.service

# Restart Nginx so that the web page is accessible.
sudo service nginx restart
sudo nginx -t
