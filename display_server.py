import multiprocessing
import gunicorn.app.base
from flask import Flask, request, Response
from queue import Empty
from multiprocessing import Queue, Event
from threading import Thread
from time import sleep
from PIL import Image, ImageDraw, ImageFont
from markupsafe import escape
import digitalio
import board
from adafruit_rgb_display import st7789
import subprocess
import json

Shift = MOD_LEFT_SHIFT = 0x02
shift_buffer = [Shift, 0, 0, 0, 0, 0, 0, 0]
#wake_buffer = [0xe0, 0, 0, 0, 0, 0, 0, 0]
coffee_buffer = [0, 0, 0xf9, 0, 0, 0, 0, 0]
empty_buffer = [0] * 8

app = Flask(__name__)
messages = Queue()
images = Queue()
connected_event = Event()

cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

# Config for display baudrate (default max is 24mhz):
BAUDRATE = 64000000

# Setup SPI bus using hardware SPI:
spi = board.SPI()

# Create the ST7789 display:
disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)

# Some constants
height = disp.width  # we swap height/width to rotate it to landscape!
width = disp.height
rotation = 270

# More constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Alternatively load a TTF font.  Make sure the .ttf font file is in the
# same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
font21 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 21)

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# Setup buttons
#buttonA = digitalio.DigitalInOut(board.D23)
#buttonB = digitalio.DigitalInOut(board.D24)
#buttonA.switch_to_input()
#buttonB.switch_to_input()

image_paths = {"blank": "display-image/checkbox-blank.png",
               "checkmark": "display-image/checkmark.png",
               "xmark": "display-image/xmark.png"}

def is_phone_connected():
    try:
        # Try and send two events to the HID keyboard 1) Shift key down, and 2) release
        # If it fails, we know a phone is not plugged in.
        keyboard = open("/dev/hidg0", "rb+")
        keyboard.seek(0)
        keyboard.write(bytearray(coffee_buffer))
        keyboard.flush()
        return True
    except BlockingIOError:
        #print("Phone is not connected.")
        return False
    except:
        return False

def server_loop():
    background_image = image_paths["blank"]
    image_to_load = image_paths["blank"]
    current_image = image_paths["blank"]
    current_offset = (0,0)
    current_message = ""

    while True:
        try:
            msg = messages.get_nowait()
            current_message = msg["message"]
            print(msg, flush=True)
        except Empty:
            pass

        try:
            img = images.get_nowait()
            current_image = image_paths[img["image"]]
            current_offset = (int(img.get("x",0)), int(img.get("y",0)))
            print(img, flush=True)
        except (Empty):
            pass
        except KeyError:
            print("Error: Image requested not found", flush=True)

        connected = is_phone_connected()
        if connected:
            connected_event.set()
        else:
            connected_event.clear()
            current_image = image_paths["blank"]
            current_offset = (0,0)
            current_message = ""

        cmd = "hostname"
        #IP = "checkbox001.local:5000"
        try:
            IP = "%s.local:5000" % subprocess.check_output(cmd, shell=True).strip().decode("utf-8")
        except:
            IP = ""

        if connected:
            ConnectedText = "Connected: Yes"
            ConnectedColor = "#00FF00"
        else:
            ConnectedText = "Connected: No"
            ConnectedColor = "#FF0000"

        # Reload the image.
        image  = Image.open(background_image)

        # Draw overlay image
        overlay_image = Image.open(current_image)
        image.paste(overlay_image, current_offset)

        # Draw the image
        draw = ImageDraw.Draw(image)

        # Write status text.
        y = top
        draw.text((x, y), IP, font=font, fill="#FFFFFF")
        y += font.getbbox(IP)[3] + 5
        draw.text((x, y), ConnectedText, font=font, fill=ConnectedColor)
        y += font.getbbox(IP)[3] + 5
        draw.text((x, y), str(current_message)[:26], font=font, fill="#0000FF")

        # Display image.
        disp.image(image, rotation)

        sleep(.5)

Thread(target=server_loop, daemon=True).start()

@app.route("/message/")
def message():
    if request.args:
        msg = request.args.get("msg","")
        messages.put_nowait({ "message": msg })
    return f"<p>Message: </p>"

@app.route("/message/<msg>")
def message2(msg):
    messages.put_nowait({ "message": msg })
    return f"<p>Message: {escape(msg)}</p>"

@app.route("/image/")
def image():
    img = "blank"
    x = 0
    y = 0
    if request.args:
        if "img" in request.args:
            img = request.args.get("img")
            if img == "":
                img = "blank"
        if "x" in request.args:
            x = request.args.get("x")
        if "y" in request.args:
            y = request.args.get("y")
    images.put_nowait({ "image": img, "x": x, "y": y})
    return f"<p>Image: {escape(img)}</p>"

@app.route("/image/<img>")
def image2(img, x=0, y=0):
    if request.args:
        x = request.args.get("x",0)
        y = request.args.get("y",0)
    data = { "image": img, "x": x, "y": y}
    images.put_nowait(data)
    return f"<p>Image: {escape(img)}</p>"

@app.route("/phone/status/")
def phone_status():
    if connected_event.is_set():
        status = {"connected": True}
    else:
        status = {"connected": False}
    return Response(mimetype="application/json", response = json.dumps(status))

class StandaloneApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

def on_exit(server):
    server.log.info("Clearing Checkbox display")
    # On exit, clear and turn off screen...
    image  = Image.open("display-image/checkbox-blank.png")
    disp.image(image, rotation)
    backlight.value = False
    server.log.info("Exiting")

if __name__ == "__main__":
    options = {
        'bind': '%s:%s' % ('0.0.0.0', '8080'),
        'workers': 1,
        'on_exit': on_exit,
        'capture_output': True
    }
    # Dev
    #app.run(host="0.0.0.0", port=8080, debug=False)
    # Prod
    StandaloneApplication(app, options).run()

    # On exit, clear and turn off screen...
    print("Clearing Checkbox display", flush=True)
    image  = Image.open("display-image/checkbox-blank.png")
    disp.image(image, rotation)
    backlight.value = False
    print("Exiting", flush=True)