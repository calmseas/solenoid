from solenoid.config import ServiceConfig
import requests
from requests.exceptions import RequestException
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import logging


class EurekaClientError(Exception):
    pass


def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


class EurekaClient:
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.session = requests_retry_session(config.clientOptions)
        self.log = logging.getLogger(__name__)

    def register(self):
        self.log.info(f'Registering {self.config.get_app()} with {self.config.get_app_url()}')
        try:
            res = self.session.post(self.config.get_app_url(), json=self.config.get_service_metadata())
        except RequestException:
            self.log.exception(f'Error registering with Eureka server {self.config.get_eureka_server_url()}')
            raise
        self.log.info(f'Response code for registration: {res.status_code}')
        if res.status_code == 204:
            self.log.info(f'successfully registered {self.config.get_app()}')
            return True
        self.log.error(f'Failed to register: {res.status_code}')
        raise EurekaClientError(f'Failed to register: {res.status_code}')

    def deregister(self):
        self.log.info(f'Deregistering {self.config.get_app()} with {self.config.get_instance_url()}')
        try:
            res = self.session.delete(self.config.get_instance_url())
        except RequestException:
            self.log.exception(f'Error deregistering with Eureka server {self.config.get_eureka_server_url()}')
            raise
        self.log.info(f'Response code for deregistration: {res.status_code}')
        if res.status_code == 200:
            self.log.info(f'successfully deregistered {self.config.get_app()}')
            return True
        self.log.error(f'Failed to deregister: {res.status_code}')
        raise EurekaClientError(f'Failed to deregister: {res.status_code}')

    def heartbeat(self):
        self.log.info(f'Sending heartbeat for {self.config.get_app()} with {self.config.get_instance_url()}')
        try:
            res = self.session.put(self.config.get_instance_url(), params={'status': 'UP'})
        except RequestException:
            self.log.exception(f'Error sending heartbeat to Eureka server {self.config.get_eureka_server_url()}')
            raise
        self.log.info(f'Response code for heartbeat: {res.status_code}')
        if res.status_code == 200:
            self.log.info(f'successful heartbeat for {self.config.get_instance_id()}')
            return True
        elif res.status_code == 404:
            self.log.error(f'instance {self.config.get_instance_id()} does not exist')
            raise EurekaClientError(f'instance {self.config.get_instance_id()} does not exist')
        self.log.error(f'Failed send heartbeat: {res.status_code}')
        raise EurekaClientError(f'Failed to send heartbeat: {res.status_code}')

    def get_all_instances(self, app: str=None):
        self.log.info(f'Retrieving all instances of {self.config.get_app()} with {self.config.get_app_url(app)}')
        try:
            res = self.session.get(self.config.get_app_url(app))
        except RequestException:
            self.log.exception(f'Error retrieving instances with Eureka server {self.config.get_eureka_server_url()}')
            raise
        self.log.info(f'Response code for registration: {res.status_code}')
        if res.status_code == 200:
            self.log.info(f'successfully retrieved instances for {self.config.get_app() if app is None else app}')
            return res.json()
        self.log.error(f'Failed to retrieve instances for {self.config.get_app() if app is None else app}: {res.status_code}')
        raise EurekaClientError(f'Failed to retrieve instances for {self.config.get_app() if app is None else app}: {res.status_code}')

    def get_app_instance(self, app: str=None, instance_id: str=None):
        self.log.info(f'Retrieving instance of {self.config.get_app()} with {self.config.get_instance_url(app, instance_id)}')
        try:
            res = self.session.get(self.config.get_instance_url(app, instance_id))
        except RequestException:
            self.log.exception(f'Error retrieving instance with Eureka server {self.config.get_eureka_server_url()}')
            raise
        self.log.info(f'Response code for registration: {res.status_code}')
        if res.status_code == 200:
            self.log.info(f'successfully retrieved instance for {self.config.get_app() if app is None else app}:'
                          f'{self.config.get_instance_id() if instance_id is None else instance_id}')
            return res.json()
        self.log.error(f'Failed to retrieve instance for {self.config.get_app() if app is None else app}:'
                       f'{self.config.get_instance_id() if instance_id is None else instance_id}')
        raise EurekaClientError(f'Failed to retrieve instance for {self.config.get_app() if app is None else app}:'
                                f'{self.config.get_instance_id() if instance_id is None else instance_id}')

    def out_of_service(self):
        self.log.info(f'Taking instance out of service for {self.config.get_app()} with {self.config.get_instance_url()}')
        try:
            res = self.session.put(self.config.get_status_url(), params={'value': 'OUT_OF_SERVICE'})
        except RequestException:
            self.log.exception(f'Error taking instance out of service with Eureka server {self.config.get_eureka_server_url()}')
            raise
        self.log.info(f'Response code for out of service request: {res.status_code}')
        if res.status_code == 200:
            self.log.info(f'successfully out of service {self.config.get_instance_id()}')
            return True
        self.log.error(f'Failed to take instance out of service: {res.status_code}')
        raise EurekaClientError(f'Failed to take instance out of service: {res.status_code}')

    def back_in_service(self):
        self.log.info(f'Taking instance out of service for {self.config.get_app()} with {self.config.get_instance_url()}')
        try:
            res = self.session.delete(self.config.get_status_url())
        except RequestException:
            self.log.exception(f'Error taking instance out of service with Eureka server {self.config.get_eureka_server_url()}')
            raise
        self.log.info(f'Response code for out of service request: {res.status_code}')
        if res.status_code == 200:
            self.log.info(f'successfully out of service {self.config.get_instance_id()}')
            return True
        self.log.error(f'Failed to take instance out of service: {res.status_code}')
        raise EurekaClientError(f'Failed to take instance out of service: {res.status_code}')

    def update_metadata(self, key, value):
        self.log.info(f'Updating instance metadata {key}={value} for {self.config.get_app()} with {self.config.get_instance_url()}')
        try:
            res = self.session.put(self.config.get_metadata_update_url(), params={key: value})
        except RequestException:
            self.log.exception(f'Error updating instance metadata with Eureka server {self.config.get_eureka_server_url()}')
            raise
        self.log.info(f'Response code for out of service request: {res.status_code}')
        if res.status_code == 200:
            self.log.info(f'successfully updated metadata for {self.config.get_instance_id()}')
            return True
        self.log.error(f'Failed to update metadata for service: {res.status_code}')
        raise EurekaClientError(f'Failed to update metadata for service: {res.status_code}')

