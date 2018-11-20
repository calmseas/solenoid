import platform, sys, socket
from solenoid.config import ServiceConfig

#TODO needs to be depth first traversal to capture a.b.c config props
def _config(key, value):
    return {
        key: {
            'value': value,
            'origin': 'Python dictionary config'
        }
    }

def get_runtime(config: ServiceConfig):
    env = {
        'activeProfiles': [],
        'propertySources': [
            {
                "name": "server.ports",
                "properties": {
                    "local.server.port": {
                        "value": config.get_port()
                    }
                }
            },
            {
                'name': 'systemProperties',
                'properties': {
                    'runtime': {
                        'value': 'Python'
                    },
                    'python.vm.version': {
                        'value': platform.python_version()
                    },
                    'python.version.string': {
                        'value': 'Python %s on %s' % (sys.version, sys.platform)
                    },
                    'python.implementation.name': {
                        'value': platform.python_implementation()
                    },
                    'platform.architecture': {
                        'value': platform.architecture()[0]
                    },
                    'python.vm.vendor': {
                        'value': 'Python Software Foundation'
                    }
                }
            }, {
                'name': 'systemEnvironment',
                'properties': {
                    'PYTHON_EXECUTABLE': {
                        'value': sys.executable,
                        'origin': 'sys module'
                    },
                    'PYTHON_HOME': {
                        'value': sys.exec_prefix,
                        'origin': 'sys module'
                    }
                }
            },
            {
                "name": "springCloudClientHostInfo",
                "properties": {
                    "spring.cloud.client.hostname": {
                        "value": platform.node()
                    },
                    "spring.cloud.client.ip-address": {
                        "value": socket.gethostbyname(socket.gethostname())
                    }
                }
            },
            {
                "name": "defaultProperties",
                "properties": {}
            }
        ]}
    return env
