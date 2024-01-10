# checkbox-display-server
A tiny server for controlling the TFT display on a Tapster Checkbox

## Install
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
