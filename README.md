# Hello Reswarm Nodejs
This is a simple "hello world" app as example for RESWARM.
It show some logs example and logs every second.

## Instructions
Each app should have at least one Dockerfile
(see: https://docs.docker.com/engine/reference/builder/) and a base code written on your favorite programming language.

### To build the source code:
- Choose a device on the list (dropdown) an press RUN.
- The "RUN" button compress the source code, sends it over to the selected device,
build the docker image and start the container.
- You should see some logs every second.

### Publishing an app:
Click on "Publish", enter the version number/name and press "Publish App"

## Available Environment Variables
**DEVICE_NAME**            current device name
**DEVICE_SERIAL_NUMBER**   the unique identifier of the device

## Data volumes
Every app has by default a directory ````/data/<your_app_name>/data```` volume that can
be used to persist data case the device resets or the app is restarted.

## Special Volumes (For hardware capabilities)

Currently the following volumes are also available for development apps:
* ````  /dev/ttyUSB0     ````    For GSM Mobile Huawei LTE USB-Stick
* ````  /dev/ttyUSB2     ````    For SIM7600E-H 4G HAT GPS, phone calls, SMS
* ````  /dev/cdc-wdm0    ````    For SIM7600E-H mobile network
* ````  /dev/ttyS0       ````    For GPS Module
* ````  /dev/ttyAMA0     ````    For the Sigfox devices
* ````  /dev/ppp         ````    For the PPP network interface unit
* ````  /dev/snd         ````    For Audio Module
* ````  /dev/spidev0.0   ````    For SPI (LED Matrix)
* ````  /dev/spidev0.1   ````    For SPI (LED Matrix)
* ````  /dev/mem         ````    For LED 7 Colors
* ````  /dev/usb         ````    For general USB usage
* ````  /dev/i2c-0       ````    For I2C interface 0
* ````  /dev/i2c-1       ````    For I2C interface 1
* ````  /dev/gpiomem     ````    For GPIO device

## Other Default Device Configuration:

````
hdmi_force_hotplug=1
enable_uart=1

# camera settings, see http://elinux.org/RPiconfig#Camera
# start_x=1
# disable_camera_led=1
# gpu_mem=128

# Enable audio (added by raspberrypi-sys-mods)
# dtparam=audio=on

# GSM Stick
max_usb_current=1
safe_mode_gpio=4

# Temperature Sensor
dtoverlay=w1-gpio,gpiopin=18

# Light Sensor
dtparam=i2c_arm=on,i2c1=on

# Activate SPI (e.g. for controlling LED band)
dtparam=spi=on```

````
