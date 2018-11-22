from .config import ServiceConfig
from .eureka import EurekaClient
from flask import Flask
from flask_cors import CORS
from .solenoid import Solenoid
import time
import datetime
from collections import deque
import logging
import signal
import sys


class Trace:
    def __init__(self, req, sess):
        self.timestamp = datetime.datetime.now()
        self.t1 = time.time()
        self.t2 = self.t1
        self.path = req.path
        self.principal = req.remote_user
        self.ipaddr = req.remote_addr
        self.scheme = req.scheme
        self.referrer = req.referrer
        self.method = req.method
        self.req_headers = {'Accept': req.content_type}
        self.url = req.url
        self.response = None
        self.status = None
        self.resp_headers = None
        self.session_id = sess.sid if hasattr(sess, 'sid') else None

    def _req_header(self, req):
        if 'Authorization' in req.headers: self.req_headers['Authorization'] = req.headers['Authorization']

    def complete(self, resp):
        self.t2 = time.time()
        self.status = resp.status_code
        self.resp_headers = {k:v for k,v in resp.headers.items()}

    def complete_exc(self):
        self.t2 = time.time()
        self.status = 500
        self.resp_headers = {}

    def render(self):
        trace = {
            'timestamp': self.timestamp.isoformat('T'),
            'request': {
                'method': self.method,
                'uri': self.url,
                'headers': self.req_headers
            },
            'response': {
                'status': self.status,
                'headers': self.resp_headers
            },
            'timeTaken': self.t2-self.t1
        }
        if self.principal is not None:
            trace['principal'] = {'name': self.principal}
        if self.session_id is not None:
            trace['session'] = {'id': self.session_id}
        return trace


class SolenoidFlaskApp:

    def __init__(self, config_file: str, cors=True):
        self.log = logging.getLogger(__name__)
        self.traces = deque(maxlen=100)
        self.config = ServiceConfig()
        self.config.load_config(config_file)
        self.app = Flask(__name__)
        if cors: CORS(self.app)
        self.client = EurekaClient(self.config)
        self.solenoid = Solenoid(self.config, self.app, self.traces)
        self.heartbeat = None

    def register_service(self):
        self.client.register()

    def start_heartbeat(self):
        from threading import Timer

        class Heartbeat(Timer):
            def run(self):
                while not self.finished.is_set():
                    self.function(*self.args, **self.kwargs)
                    self.finished.wait(self.interval)

        self.heartbeat = Heartbeat(30.0, self.client.heartbeat)
        self.heartbeat.setDaemon(True)
        self.heartbeat.start()  # every 30 seconds, call heartbeat

    def run(self):
        self.app.run('0.0.0.0', self.config.get_port())

    def route(self, rule, **options):
        def decorator(f):
            endpoint = options.pop('endpoint', None)
            self.app.add_url_rule(rule, endpoint, f, **options)
            return f
        return decorator

    def trace(self, rule, **options):
        def decorator(f):
            def wrapped_f(*args):
                from flask import request, session

                self.log.debug(f'Beginning HTTP trace for {request.path}')
                t = Trace(request, session)
                try:
                    resp = f(*args)
                except Exception:
                    self.log.exception(f'Exception during HTTP trace for {request.path}')
                    t.complete_exc()
                    self.traces.append(t)
                    raise
                t.complete(resp)
                self.traces.append(t)
                self.log.debug(f'Finished HTTP trace for {request.path} -> status code:')
                return resp

            endpoint = options.pop('endpoint', None)
            self.app.add_url_rule(rule, endpoint, wrapped_f, **options)

            return wrapped_f

        return decorator


