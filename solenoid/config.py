import json, os.path, yaml
import logging
from typing import Dict


def _url_or_path(url):
    if url is None:
        return None
    elif url.startsWith('http'):
        return url[url.index('/', 8):]
    return url


class ConfigError(Exception):
    pass


class DataCenterInfo:
    def __init__(self, cls, name):
        self.cls = cls
        self.name = name

    def render(self):
        return {
            '@class': self.cls,
            'name': self.name
        }

myOwnDC = DataCenterInfo('com.netflix.appinfo.InstanceInfo$DefaultDataCenterInfo', 'MyOwn')

class Port:
    def __init__(self, port: int, enabled: bool):
        self.port = port
        self.enabled = enabled

    def render(self):
        return {
            '$': self.port,
            '@enabled': self.enabled
        }


class ServiceMetadata:

    def __init__(self, instanceId: str, hostName: str, app: str, vipAddress: str, secureVipAddress: str, ipAddr: str,
                 status: str, port: Port, securePort: Port,
                 healthCheckUrl: str = None, healthCheckPath: str=None, statusPageUrl: str = None, statusPagePath: str=None,
                 homePageUrl: str = None, homePagePath: str=None,
                 dataCenterInfo: DataCenterInfo = myOwnDC):
        self.instanceId = instanceId
        self.hostName = hostName
        self.app = app
        self.vipAddress = vipAddress
        self.secureVipAddress = secureVipAddress
        self.ipAddr = ipAddr
        self.status = status
        self.port = port
        self.securePort = securePort
        self.healthCheckUrl = healthCheckUrl
        self.healthCheckPath = healthCheckPath is not None if healthCheckPath else _url_or_path(healthCheckUrl)
        self.statusPageUrl = statusPageUrl
        self.statusPagePath = statusPagePath is not None if statusPageUrl else _url_or_path(statusPageUrl)
        self.homePageUrl = homePageUrl
        self.homePagePath = homePagePath is not None if homePagePath else _url_or_path(homePageUrl)
        self.dataCenterInfo = dataCenterInfo

    def render(self):
        return {
            'instance': {
                'instanceId': self.instanceId,
                'hostName': self.hostName,
                'app': self.app,
                'ipAddr': self.ipAddr,
                'vipAddress': self.vipAddress,
                'secureVipAddress': self.secureVipAddress,
                'status': self.status,
                'port': self.port.render(),
                'securePort': self.securePort.render(),
                'statusPageUrl': self.statusPageUrl,
                'healthCheckUrl': self.healthCheckUrl,
                'homePageUrl': self.healthCheckUrl,
                'dataCenterInfo': self.dataCenterInfo.render()
            }
        }

    def render_json(self):
        return json.dumps(self.render())


class DiscoveryServer:

    def __init__(self, hostName: str, port: int, ssl: bool, servicePath: str):
        self.hostName = hostName
        self.port = port
        self.ssl = ssl
        self.servicePath = servicePath


class ClientOptions:

    def __init__(self, requestImpl: str, maxRetries: int = 3,
                 heartBeatIntervalInSecs: int = 30000, registryFetchIntervalInSecs: int = 30000,
                 registerWithEureka: bool = True):
        self.requestImpl = requestImpl
        self.maxRetries = maxRetries
        self.heartBeatIntervalInSecs = heartBeatIntervalInSecs
        self.registryFetchIntervalInSecs = registryFetchIntervalInSecs
        self.registerWithEureka = registerWithEureka


class ServiceConfig:

    def __init__(self, serviceMetadata: ServiceMetadata = None,
                 discoveryServer: DiscoveryServer = None,
                 options: ClientOptions = None):
        self.log = logging.getLogger(__name__)
        self.serviceMetadata = serviceMetadata
        self.discoveryServer = discoveryServer
        self.clientOptions = options
        self.fileConfig = None
        self.configfile = None

    def load_config(self, config_file):
        self.configfile = config_file
        if os.path.exists(config_file):
            self.log.debug(f'Loading Eureka configuration file: {config_file}')
            with open(config_file, 'rt') as f:
                try:
                    self.fileConfig = yaml.safe_load(f.read())
                except yaml.YAMLError as exc:
                    self.log.exception(f'Error loading Eureka configuration file: {config_file}')
                    raise
                self.log.debug(self.fileConfig)
        else:
            raise FileNotFoundError(f'Could not load config file: {config_file}')

    def get_option(self, option):
        if self.fileConfig is not None:
            try:
                return self.fileConfig['options'][option]
            except KeyError:
                self.log.exception(f'could not find option:{option} in configuration')
                raise ConfigError(f'could not find option:{option} in configuration')
        return getattr(self.clientOptions, option)

    def get_app(self):
        if self.fileConfig is not None:
            try:
                return self.fileConfig['instance']['app']
            except KeyError:
                self.log.exception('could not find app in configuration')
                raise ConfigError('could not find app in configuration')
        return self.serviceMetadata.app

    def get_instance_id(self):
        if self.fileConfig is not None:
            try:
                return self.fileConfig['instance']['instanceId']
            except KeyError:
                self.log.exception('could not find instanceId in configuration')
                raise ConfigError('could not find instanceId in configuration')
        return self.serviceMetadata.instanceId

    def get_service_metadata(self) -> Dict:
        if self.fileConfig is not None:
            try:
                return {'instance': self.fileConfig['instance']}
            except KeyError:
                self.log.exception('instance block missing from configuration')
                raise ConfigError('instance block missing from configuration')
        return self.serviceMetadata.render()

    def get_service_metadata_json(self) -> str:
        try:
            return json.dumps(self.get_service_metadata())
        except Exception as exc:
            self.log.exception('Error serialising metadata to JSON')
            raise exc

    def get_eureka_server_url(self) -> str:
        if self.fileConfig is not None:
            try:
                host = self.fileConfig['eureka']['host']
                port = self.fileConfig['eureka']['port']
                ssl = self.fileConfig['eureka']['ssl']
                servicePath = self.fileConfig['eureka']['servicePath']
            except KeyError as exc:
                self.log.exception('Eureka server block misconfigured')
                raise ConfigError('Eureka server block misconfigured')
        else:
            host = self.discoveryServer.hostName
            port = self.discoveryServer.port
            ssl = self.discoveryServer.ssl
            servicePath = self.discoveryServer.servicePath
        proto = 'https' if ssl else 'http'
        return f'{proto}://{host}:{port}{servicePath}'

    def get_app_url(self, app: str=None):
        if app is not None:
            return f'{self.get_eureka_server_url()}/{app}'
        return f'{self.get_eureka_server_url()}/{self.get_app()}'

    def get_instance_url(self, app: str=None, instance_id: str=None):
        if app is not None and instance_id is not None:
            return f'{self.get_eureka_server_url()}/{app}/{instance_id}'
        return f'{self.get_eureka_server_url()}/{self.get_app()}/{self.get_instance_id()}'

    def get_status_url(self, app: str=None, instance_id: str=None):
        if app is not None and instance_id is not None:
            return f'{self.get_eureka_server_url()}/{app}/{instance_id}/status'
        return f'{self.get_eureka_server_url()}/{self.get_app()}/{self.get_instance_id()}/status'

    def get_metadata_update_url(self, app: str=None, instance_id: str=None):
        if app is not None and instance_id is not None:
            return f'{self.get_eureka_server_url()}/{app}/{instance_id}/metadata'
        return f'{self.get_eureka_server_url()}/{self.get_app()}/{self.get_instance_id()}/metadata'

    def get_home_page_path(self):
        if self.fileConfig is not None:
            try:
                return self.fileConfig['instance']['homePagePath']
            except KeyError:
                self.log.exception('could not find homePagePath in configuration')
                raise ConfigError('could not find homePagePath in configuration')
        return self.serviceMetadata.homePagePath

    def get_health_check_path(self):
        if self.fileConfig is not None:
            try:
                return self.fileConfig['instance']['healthCheckPath']
            except KeyError:
                self.log.exception('could not find healthCheckPath in configuration')
                raise ConfigError('could not find healthCheckPath in configuration')
        return self.serviceMetadata.healthCheckPath

    def get_status_page_path(self):
        if self.fileConfig is not None:
            try:
                return self.fileConfig['instance']['statusPagePath']
            except KeyError:
                self.log.exception('could not find statusPagePath in configuration')
                raise ConfigError('could not find statusPagePath in configuration')
        return self.serviceMetadata.statusPagePath

    def get_host_url(self):
        if self.fileConfig is not None:
            try:
                hostname = self.fileConfig['instance']['hostName']
                port = self.fileConfig['instance']['port']['$']
            except KeyError:
                self.log.exception('could not find host or port in configuration')
                raise ConfigError('could not find host or port in configuration')
        else:
            hostname = self.serviceMetadata.hostName
            port = self.serviceMetadata.port
        return f'http://{hostname}:{port}'

    def get_port(self):
        if self.fileConfig is not None:
            try:
                return self.fileConfig['instance']['port']['$']
            except KeyError:
                self.log.exception('could not find port in configuration')
                raise ConfigError('could not find port in configuration')
        return self.serviceMetadata.port
