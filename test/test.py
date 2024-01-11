import requests

image_url =  "http://localhost:8080/image/"
message_url = "http://localhost:8080/message/"
status_url = "http://localhost:8080/phone/status/"

"""
# To run:
python -i test.py

# Show image centered horizontally, at bottom of screen
>>> image("checkmark", x=84, y=63)
>>> image("xmark", x=84, y=63)

# Clear the image
>>> image()
or
>>> image("blank")

# Show a message
>>> message("Hello, World!")

# Clear the message
>>> message()
or
>>> message("")

# Get phone status
>>> status()
{'connected': True}
"""


def image(img = "blank", x=0, y=0):
    r = requests.get(image_url, {"img": img, "x":x, "y":y})

def message(msg = ""):
    r = requests.get(message_url, {"msg": msg})

def status():
    r = requests.get(status_url)
    return r.json()

if __name__ == "__main__":
    image("checkmark", x=84, y=63)
    message("Hello, World!")
    print(status())