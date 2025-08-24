# mqtt-bh1750

This script allows you to collect data from a BH1750 ambient light sensor using a Raspberry Pi through [MQTT](https://mqtt.org/)

- Utilizes the [`smbus`](https://pypi.org/project/smbus/) python package
- Integrates seamessly with Home Assistant through MQTT

> **Credit:** Inspired by and adapted from [tofuSCHNITZEL's rpi-screenbrightness-mqtt](https://github.com/tofuSCHNITZEL/rpi-screenbrightness-mqtt/blob/master/rpi_screenbrightness_mqtt/run.py). Many thanks for the great foundation!

## Features

- Publishes the current ambient light (in lux)
- Automatic Home Assistant MQTT Discovery support
  - Automatically configures itself as a valid device and adds itself as an illuminance sensor
- Designed to run on Raspberry Pi

<p align="center">
  <img src="https://github.com/user-attachments/assets/b2cc7ad6-013d-45a5-b95f-c0a3d6e7ebf5" style="height:400px" />
</p>

## Configuration

Using the given `settings.conf.example` file, create a `settings.conf` file in the root of the project directory

- Fill out its information according to the comments
- More information regarding the `device` field can be found [here](https://www.home-assistant.io/integrations/mqtt/#discovery-examples-with-component-discovery)

Or as an example:

```ini
device = {"name": "Raspberry Pi 4", "identifiers": "pi", "manufacturer": "Raspberry Pi Foundation", "model": "4B"}
```

## Building/Running

Run the provided docker build script `./build.sh` to build the docker image

Here are examples of running the container through docker:

### Docker CLI

```bash
docker run -d \
  --privileged \
  -v /dev/i2c-1:/dev/i2c-1 \
  -v /PATH/TO/REPO/settings.conf:/app/settings.conf \
  bh1750-mqtt
```

### Docker Compose

```yaml
bh1750:
  image: bh1750-mqtt
  volumes:
    - /dev/i2c-1:/dev/i2c-1
    - /PATH/TO/REPO/settings.conf:/app/settings.conf
  privileged: true # needed to access the GPIO
```

> [!NOTE]
> The container might need the `privileged` flag in order to properly access the device's GPIO pins. There might be a better way to do this without giving root access, but I found this to be the easiest method
