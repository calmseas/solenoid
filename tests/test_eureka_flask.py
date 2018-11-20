import unittest
import logging
import logging.config
import os
import os.path
import yaml

from eureka.client.config import EurekaConfig
from eureka.client.flask import EurekaFlaskApp
from flask import Flask, jsonify
from flask_cors import CORS


import eureka.client.api as api


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
        app = Flask(__name__)
        CORS(app)
        config = EurekaConfig()
        config.load_config('service.yaml')
        efapp = EurekaFlaskApp(config, app)

        @efapp.app.route('/', methods=['GET'])
        def home():
            resp = jsonify({'test':'client'})
            resp.status_code = 200
            return resp

        efapp.app.run('0.0.0.0', config.get_port())
