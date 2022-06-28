cd
sudo snap install core; sudo snap refresh core
sudo apt-get remove certbot
sudo snap install --classic certbot
sudo snap refresh certbot
sudo rm /usr/bin/certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot

# Update the "/etc/nginx/sites-enabled/flask_app" config file for Nginx.
# NOTE: It is necessary that the server is allowed to receive HTTPS requests from anywhere.
#   Check the server's network security group to see if this is the case.
sudo certbot --nginx -n -d www.shareableevents.com --agree-tos

sudo ufw allow https
sudo ufw allow 'Nginx Full'
sudo systemctl restart nginx