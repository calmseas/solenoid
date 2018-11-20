from .config import EurekaConfig
from .api import EurekaClientRequests
from flask import Flask, request
from .actuator import Actuator


class EurekaFlaskApp:

    def __init__(self, config: EurekaConfig, app: Flask):
        self.config = config
        self.app = app
        self.client = EurekaClientRequests(config)
        self.actuator = Actuator(config, app)
        self.client.register()



    def register_service(self):
        pass

    def start_heartbeat(self):
        pass

