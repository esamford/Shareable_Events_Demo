# A shell script to make cloning the repository easier. Copy this to "/home/[admin_username]/" before running it.
# NOTE: If anything goes wrong with Nginx or Gunicorn, you can try debugging with the following commands:
#   sudo systemctl status gunicorn
#   sudo systemctl status nginx

# Download the repo from GitHub and install required Python code.
cd /home/ubuntu
rm -rf Shareable_Events
git clone git@github.com:esamford/Shareable_Events.git
sudo chown -R ubuntu Shareable_Events
sudo chmod 777 Shareable_Events
cd /home/ubuntu
source Shareable_Events/server_files/update_server_packages.sh
cd /home/ubuntu
source Shareable_Events/server_files/project_setup.sh
cd /home/ubuntu
source Shareable_Events/server_files/setup_nginx_and_gunicorn.sh
cd /home/ubuntu
source Shareable_Events/server_files/update_SSL_certificate.sh
cd /home/ubuntu
source Shareable_Events/server_files/restart_web_app.sh
cd /home/ubuntu
