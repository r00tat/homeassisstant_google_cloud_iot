"""Google Cloud IoT Integration"""
# import homeassistant.loader as loader
import logging
from .config import DOMAIN
from .controller import IoTController

# List of integration names (string) your integration depends upon.
DEPENDENCIES = ['mqtt', 'mqtt_refresh']

log = logging.getLogger(DOMAIN)


def setup(hass, config):
    """Set up the Hello MQTT component."""
    try:
        IoTController(hass, config)
        return True
    except:  # noqa
        log.exception("failed to initialize iot connection")
        return False
