from flask import Flask, Response, make_response
from flask.json import dumps, request
from .solenoids import log, health, runtime
from .config import ServiceConfig
import logging
from collections import deque

CONTENT_TYPE = 'application/vnd.spring-boot.actuator.v2+json;charset=UTF-8'


def shutdown_server():
    '''
    Function to gracefully shutdown server. Only works with DEV Flask server
    :return: None
    '''
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


class Solenoid:

    def __init__(self, config: ServiceConfig, app: Flask, httptraces: deque):
        self.app = app
        self.config = config
        self.traces = httptraces
        self.log = logging.getLogger(__name__)

        @app.route('/actuator')
        def actuator():
            return Response(dumps(
                {
                    '_links': {
                        'self': f'{self.config.get_host_url()}/actuator',
                        'templated': False
                    },
                    'health': {
                        'self': f'{self.config.get_host_url()}{self.config.get_health_check_path()}',
                        'templated': False
                    },
                    'info': {
                        'self': f'{self.config.get_host_url()}{self.config.get_status_page_path()}',
                        'templated': False
                    },
                    'logfile': {
                        'self': f'{self.config.get_host_url()}/actuator/logfile',
                        'templated': False
                    },
                    'loggers': {
                        'self': f'{self.config.get_host_url()}/actuator/loggers',
                        'templated': False
                    },
                    'env': {
                        'self': f'{self.config.get_host_url()}/actuator/env',
                        'templated': False
                    },
                    'shutdown': {
                        'self': f'{self.config.get_host_url()}/actuator/shutdown',
                        'templated': False
                    }
                }
            ), mimetype=CONTENT_TYPE)

        @app.route(self.config.get_status_page_path())
        def status():
            return Response(dumps({'status':'UP'}), mimetype=CONTENT_TYPE)

        @app.route(self.config.get_health_check_path())
        def health_check():
            return Response(dumps({'status':'UP', 'details': {'diskSpace': health.get_disk_health('/')}}), mimetype=CONTENT_TYPE)

        @app.route('/actuator/logfile')
        def logfile():
            l = log.get_log()
            if l is None:
                print('No log file configured!')
            return Response(l, mimetype='text/plain')

        @app.route('/actuator/loggers')
        def loggers():
            return Response(dumps(log.get_loggers()), mimetype=CONTENT_TYPE)

        @app.route('/actuator/loggers/<logger>', methods=['POST'])
        def set_logger_level(logger):
            self.log.info(f'Setting log level for {logger} to {request.json["configuredLevel"]}')
            log.set_logger_level(logger, request.json['configuredLevel'])
            return make_response(('', 204))

        @app.route('/actuator/env')
        def env():
            return Response(dumps(runtime.get_runtime(self.config)), mimetype=CONTENT_TYPE)

        @app.route('/actuator/shutdown', methods=['POST'])
        def shutdown():
            shutdown_server()
            return Response(dumps({'message' : 'Shutting down, bye...'}), mimetype=CONTENT_TYPE)

        @app.route('/actuator/httptrace')
        def httptrace():
            traces = { 'traces': [t.render() for t in self.traces] }
            return Response(dumps(traces), mimetype=CONTENT_TYPE)


