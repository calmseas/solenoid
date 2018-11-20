import unittest
import logging
import logging.config
import os
import os.path
import yaml

from solenoid.config import ServiceConfig, ServiceMetadata, DiscoveryServer, Port, myOwnDC
import solenoid as api


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

conf = {
    "instance": {
        "instanceId": "192.168.0.1:plugin-test-aaa-service:80",
        "hostName": "192.168.0.1",
        "app": "plugin-test-aaa-service",
        "ipAddr": "192.168.0.1",
        "vipAddress": "plugin-test-aaa-service",
        "status": "UP",
        "port": {
            "$": 80,
            "@enabled": True,

        },
        "securePort": {
            "$": 443,
            "@enabled": False,

        },
        "homePageUrl": None,
        "statusPageUrl": "http://192.168.0.1:80/plugin-test/aaa-service/hello",
        "healthCheckUrl": None,
        "dataCenterInfo": {
            "@class": "com.netflix.appinfo.MyDataCenterInfo",
            "name": "MyOwn"
        },
        'leaseInfo': {
            'renewalIntervalInSecs': 15,
            'durationInSecs': 60
        }
    }
}

service = ServiceMetadata(
    instanceId='127.0.0.1:test-metadata:2020',
    hostName='localhost',
    app='test-metadata',
    ipAddr='127.0.0.1',
    vipAddress='test-metadata',
    secureVipAddress='test-metadata',
    status='UP',
    port=Port(port=2020, enabled=True),
    securePort=Port(port=2021, enabled=False),
    statusPageUrl='http://localhost:2020/info',
    dataCenterInfo=myOwnDC
)

server = DiscoveryServer(
    hostName='localhost',
    port=9091,
    ssl=False,
    servicePath='/solenoid/apps/'
)

class_config = ServiceConfig(service, server)

class MyTestCase(unittest.TestCase):
    def test_config(self):
        log = logging.getLogger(__name__)
        config = ServiceConfig()
        config.load_config('service.yaml')
        log.debug(config.get_service_metadata())

    def test_register(self):
        log = logging.getLogger(__name__)
        config = ServiceConfig()
        config.load_config('service.yaml')
        api.register(config)

    def test_eureka(self):
        import requests
        log = logging.getLogger(__name__)
        res = requests.post('http://localhost:9091/solenoid/apps/plugin-test-aaa-service', json=conf)
        log.debug(res)

    def test_class_config(self):
        api.register(class_config)


if __name__ == '__main__':
    setup_logging()
    unittest.main()
