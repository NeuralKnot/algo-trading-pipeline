# Install app dependencies
sudo apt-get -f --assume-yes install
sudo apt-get --assume-yes install python3-tk
sudo apt-get --assume-yes install python3-pip
sudo apt-get --assume-yes install xvfb
pip3 install -r /home/ubuntu/requirements.txt

# Make necessary folders
sudo mkdir -p /home/ubuntu/db
sudo mkdir -p /home/ubuntu/logs

# Selenium stuff
sudo apt-get install libxss1 libappindicator1 libindicator7
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome*.deb
sudo apt-get install -f
sudo apt-get install xvfb
sudo apt-get install unzip
wget -N http://chromedriver.storage.googleapis.com/2.26/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
chmod +x chromedriver
sudo mv -f chromedriver /usr/local/share/chromedriver
sudo ln -s /usr/local/share/chromedriver /usr/local/bin/chromedriver
sudo ln -s /usr/local/share/chromedriver /usr/bin/chromedriver

# Give ubuntu user access to everything
sudo chown -R ubuntu /home/ubuntu

# One last dependency installation
sudo apt-get -f --assume-yes install

# Add cronjob
grep "python3 /home/ubuntu/scripts/checklogs.py" /etc/crontab || echo "0 * * * * ubuntu python3 /home/ubuntu/scripts/checklogs.py" >> /etc/crontab

# Download NLTK corpus
sudo su ubuntu -c "(cd /home/ubuntu && python3 -c \"import nltk;nltk.download('wordnet')\")"

# Run app command as ubuntu
# This is in the bg, as CodeDeploy wants this script to terminate.
sudo su ubuntu -c "(cd /home/ubuntu && source scripts/env.sh && python3 main.py) > /dev/null 2> /dev/null < /dev/null &"
