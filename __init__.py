import homeassistant.loader as loader
import logging
import json
import yaml

# The domain of your component. Should be equal to the name of your component.
DOMAIN = 'google_cloud_iot'

# List of integration names (string) your integration depends upon.
DEPENDENCIES = ['mqtt']

DEFAULT_TOPIC = 'home-assistant/hello_mqtt'

log = logging.getLogger("iot")


def setup(hass, config):
    """Set up the Hello MQTT component."""
    try:
        return setup_iot(hass, config)
    except:  # noqa
        log.exception("failed to initialize iot connection")
        return False


def config_message_factory(hass, config):
    """ factory method for config message """

    def iot_config_message(msg):
        """ got iot message """
        log.info("received iot config message: %s", msg.payload)
        data = None
        try:
            data = json.loads(msg.payload)
        except:
            pass
        try:
            data = yaml.safe_load(msg.payload)
        except:
            pass
        if data:
            log.info("new dynamic iot config: %s", json.dumps(data))
            hass.states.set('{}.dynamic_config'.format(DOMAIN), json.dumps(data))

    return iot_config_message


def setup_iot(hass, config):
    """ run iot setup """
    mqtt = hass.components.mqtt
    domain_config = config[DOMAIN]
    iot_topic = domain_config.get("topic", DEFAULT_TOPIC)
    iot_config_topic = domain_config.get("topics", {}).get('config')
    entity_id = '{}.last_message'.format(DOMAIN)

    # Listener to be called when we receive a message.
    # The msg parameter is a Message object with the following members:
    # - topic, payload, qos, retain
    def iot_message(msg):
        """ iot message received """
        log.info("received iot message: %s", msg.payload)
        try:
            data = json.loads(msg.payload)
            service = data.get("service", "unkown")
            if data.get("domain"):
                domain = data.get("domain")
            else:
                service_split = service.split(".")
                domain = service_split[0]
                service = service_split[1]
            if hass.services.has_service(domain, service):
                log.info("calling service %s.%s with data %s", domain, service, data.get("data"))
                hass.services.call(domain, service, data.get("data"))
            else:
                log.warn("service %s.%s not found!", domain, service)
        except:  # noqa
            log.exception("failed to parse iot message %s", msg.payload)

    log.info("subscribing to iot topic %s", iot_topic)
    mqtt.subscribe(iot_topic, iot_message)

    if iot_config_topic:
        log.info("subscribing to iot config topic %s", iot_config_topic)
        mqtt.subscribe(iot_config_topic, config_message_factory(hass, config), 1)

    # Set the initial state.
    hass.states.set(entity_id, 'No messages')

    # Service to publish a message on MQTT.
    def set_state_service(call):
        """Service to send a message."""
        mqtt.publish(topic, call.data.get('new_state'))

    # Register our service with Home Assistant.
    hass.services.register(DOMAIN, 'set_state', set_state_service)

    # Return boolean to indicate that initialization was successfully.
    return True
