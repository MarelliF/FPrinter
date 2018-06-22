import Adafruit_DHT

from . import constants


class Temperature:

    def __init__(self, event_handler, tmp_pin):
        self.fire_event = event_handler
        self.pin = tmp_pin

    def update(self):
        humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, self.pin)
        if temperature is None:
        	self.fire_event((constants.Event.TEMPERATURE_ERROR, self.pin))
        elif temperture > constants.THRESHOLD_TEMPERATURE: 
            self.fire_event((constants.Event.OVERHEAT, self.pin))
