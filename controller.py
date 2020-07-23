import logging
import json
import yaml
from .config import DOMAIN, DEFAULT_TOPIC

log = logging.getLogger(DOMAIN)


def parse_payload(payload):
    """ parse message payload """
    data = None
    try:
        data = json.loads(payload)
    except:  # noqa
        try:
            data = yaml.safe_load(payload)
        except:  # noqa
            pass
    return data


class IoTController(object):

    def __init__(self, hass, config):
        """ run iot setup """
        self.hass = hass
        self.config = config
        self.mqtt = hass.components.mqtt
        self.domain_config = config[DOMAIN]
        self.config_topics = self.domain_config.get("topics", {})
        self.iot_commands_topic = self.config_topics.get("commands", DEFAULT_TOPIC)
        self.iot_config_topic = self.config_topics.get('config')
        self.iot_events_topic = self.config_topics.get('events')
        self.domain_filter = self.domain_config.get('domain_filter')
        self.service_filter = self.domain_config.get('service_filter')
        entity_id = '{}.last_message'.format(DOMAIN)

        log.info("subscribing to iot topic %s", self.iot_commands_topic)
        self.mqtt.subscribe(self.iot_commands_topic, self.iot_message)

        if self.iot_config_topic:
            log.info("subscribing to iot config topic %s", self.iot_config_topic)
            self.mqtt.subscribe(self.iot_config_topic, self.iot_config_message, 1)

        # Set the initial state.
        self.hass.states.set(entity_id, 'No messages')

        # Register our service with Home Assistant.
        self.hass.services.register(DOMAIN, 'publish_event', self.publish_event_service)

    def extract_service(self, data):
        """extract service from msg"""
        domain = None
        service = data.get("service", "unkown")
        if data.get("domain"):
            domain = data.get("domain")
        elif "." in service:
            (domain, service) = service.split(".", 1)
        return (domain, service)

    def is_call_allowed(self, domain, service):
        """check if service calls should be filtered"""
        if self.domain_filter and domain not in self.domain_filter:
            return False

        if self.service_filter and "{}.{}".format(domain, service) not in self.service_filter:
            return False

        return True

    def call_service(self, domain, service, payload):
        """ call another hass service """
        if self.hass.services.has_service(domain, service):
            if self.is_call_allowed(domain, service):
                log.info("calling service %s.%s with data %s", domain, service, payload)
                self.hass.services.call(domain, service, payload)
            else:
                log.warn("call to service %s.%s not allowed by filter", domain, service)
        else:
            log.warn("service %s.%s not found!", domain, service)

    # Listener to be called when we receive a message.
    # The msg parameter is a Message object with the following members:
    # - topic, payload, qos, retain
    def iot_message(self, msg):
        """ iot message received """
        log.info("received iot message: %s", msg.payload)
        data = parse_payload(msg.payload)

        try:
            if data:
                self.hass.bus.fire("{}_message".format(DOMAIN), data)
                (domain, service) = self.extract_service(data)
        except:  # noqa
            log.exception("failed to parse iot message %s", msg.payload)

        try:
            self.call_service(domain, service, data.get("data", {}))
        except:  # noqa
            log.exception("failed to call service %s", msg.payload)

    # Service to publish a message on MQTT.
    def publish_event_service(self, call):
        """Service to send a message."""
        self.mqtt.publish(self.iot_events_topic, call.data.get('new_state'))

    def iot_config_message(self, msg):
        """ got iot message """
        log.info("received iot config message: %s", msg.payload)
        data = None
        data = parse_payload(msg.payload)
        if data:
            log.info("new dynamic iot config: %s", json.dumps(data))
            self.hass.bus.fire("{}_config".format(DOMAIN), data)
            self.hass.states.set('{}.dynamic_config'.format(DOMAIN), json.dumps(data))
