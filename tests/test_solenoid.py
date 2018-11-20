import unittest
import logging
import logging.config
import os
import os.path
import yaml

from solenoid.app import SolenoidFlaskApp
from flask import jsonify


def setup_logging(
    default_path='logging.yaml',
    default_level=logging.DEBUG,
    env_key='LOG_CFG'
):
    """Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f.read())
            print(config)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


class MyTestCase(unittest.TestCase):
    def test_flask(self):
        setup_logging('logging.yaml')
        log = logging.getLogger(__name__)
        solenoid = SolenoidFlaskApp('service.yaml')

        @solenoid.route('/', methods=['GET'])
        def home():
            resp = jsonify({'test':'client'})
            resp.status_code = 200
            return resp

        @solenoid.trace('/booking', methods=['GET'])
        def booking():
            resp = jsonify({'bookings': [1,2,3,4,5]})
            resp.status_code = 200
            return resp

        solenoid.register_service()
        solenoid.start_heartbeat()
        solenoid.run()
