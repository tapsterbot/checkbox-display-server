# checkbox-display-server
A tiny server for controlling the TFT display on a Tapster Checkbox

## Set-up
```console
sudo apt update
sudo apt upgrade
sudo apt install -y python3-pip python3.11-venv python3-pil python3-numpy
sudo apt install -y --upgrade python3-setuptools
sudo apt install -y fonts-dejavu
sudo apt install -y i2c-tools libgpiod-dev python3-libgpiod

sudo raspi-config nonint do_spi 0

git clone https://github.com/tapsterbot/checkbox-display-server.git
cd checkbox-display-server

python -m venv env --system-site-packages
source env/bin/activate

python3 -m pip install --upgrade --force-reinstall spidev
python3 -m pip install --upgrade -r requirements.txt
```

## Run
```console
cd checkbox-display-server
source env/bin/activate
python display_server.py
```

## Install and run as a system service
```console
cd checkbox-display-server/service
sudo cp checkbox-display-server.service /etc/systemd/system/checkbox-display-server.service
sudo chmod 644 /etc/systemd/system/checkbox-display-server.service

# Update systemd
sudo systemctl daemon-reload

# Start
sudo systemctl start checkbox-display-server

# To make it run on boot
sudo systemctl enable checkbox-display-server
```

## Other useful system service commands
```console
# Restart
sudo systemctl restart checkbox-display-server

# Stop
sudo systemctl stop checkbox-display-server

# Get current status
sudo systemctl status checkbox-display-server

# Tail the logs
journalctl -u checkbox-display-server -f
```
