#!/usr/bin/env python

from __future__ import unicode_literals

"""
@package status_handler
@file status_handler.py
@author Edna Donoughe (based on work of James Case)
@brief gunicorn service supporting request for all routes in OOI UI Flask App, then process each static route for execution status
"""

import multiprocessing
import gunicorn.app.base
from gunicorn.six import iteritems
from os.path import exists
import psycopg2
import psycopg2.extras
import simplejson as json
from simplejson.compat import StringIO
import yaml
import requests

KEY_SERVICE = "service"
ALIVE = "alive"
CHECK_CONNECTIONS = "checkconnections"
FETCH_STATS = "fetchstats"

CONTENT_TYPE_JSON = [('Content-type', 'text/json')]
CONTENT_TYPE_TEXT = [('Content-type', 'text/html')]
OK_200 = '200 OK'
BAD_REQUEST_400 = '400 Bad Request'

class StatusHandler(gunicorn.app.base.BaseApplication):

    wsgi_url              = None
    wsgi_port             = None
    routes_url            = None
    routes_port           = None
    routes_command        = None
    routes_timeout_connect= None
    routes_timeout_read   = None
    postgresql_host       = None
    postgresql_port       = None
    postgresql_username   = None
    postgresql_password   = None
    postgresql_database   = None
    uframe_url            = None
    uframe_port           = None
    uframe_username       = None
    uframe_password       = None
    service_mode          = None

    options = None
    debug   = False


    def __init__(self, app, options=None):
        self.options = options or {}

        # Open the status_settings.yml
        settings = None
        try:
            if exists("status_settings.yml"):
                stream = open("status_settings.yml")
                settings = yaml.load(stream)
                stream.close()
            else:
                raise IOError('No settings.yml or settings_local.yml file exists!')
        except IOError, err:
            print 'IOError: %s' % err.message

        self.wsgi_url = settings['status_handler']['wsgi_server']['url']
        self.wsgi_port = settings['status_handler']['wsgi_server']['port']

        self.routes_url = settings['status_handler']['wsgi_server']['routes_url']
        self.routes_port = settings['status_handler']['wsgi_server']['routes_port']
        self.routes_command = settings['status_handler']['wsgi_server']['routes_command']
        self.routes_timeout_connect = settings['status_handler']['wsgi_server']['routes_timeout_connect']
        self.routes_timeout_read = settings['status_handler']['wsgi_server']['routes_timeout_read']

        self.postgresql_host = settings['status_handler']['postgresql_server']['host']
        self.postgresql_port = settings['status_handler']['postgresql_server']['port']
        self.postgresql_username = settings['status_handler']['postgresql_server']['username']
        self.postgresql_password = settings['status_handler']['postgresql_server']['password']
        self.postgresql_database = settings['status_handler']['postgresql_server']['database']

        self.service_mode = settings['status_handler']['service_mode']

        # override inital host:port with configuration values
        self.options['bind'] = self.wsgi_url + ':' + str(self.wsgi_port)

        self.startup()

    def startup(self):
        """
        Start status handler service to determine route execution performance.
        list of route(s) to be processed is determined dynamically from result of route_command
        """
        try:
            super(StatusHandler, self).__init__()
            
        except IOError, err:
            print "IOError: %s " % err
        except Exception, err:
            print "Exception: %s " % err

    def application(self, environ, start_response):
        request = environ['PATH_INFO']
        request = request[1:]
        print request
        output = ''
        req = request.split("&")
        param_dict = {}
        if len(req) > 1:
            for param in req:
                params = param.split("=")
                param_dict[params[0]] = params[1]
        else:
            if "=" in request:
                params = request.split("=")
                param_dict[params[0]] = params[1]
            else:
                start_response(OK_200, CONTENT_TYPE_TEXT)
                return ['<b>' + request + '</br>' + output + '</b>']

        if KEY_SERVICE in param_dict:
            # Simply check if the service is responding (alive)
            # Returns: html
            if param_dict[KEY_SERVICE] == ALIVE:
                input_str={'Service Response': 'Alive'}
                start_response(OK_200, CONTENT_TYPE_JSON)
                return self.format_json(input_str)

            # Check the postgresql connections
            # Returns: html
            elif param_dict[KEY_SERVICE] == CHECK_CONNECTIONS:
                #TODO: Add UFRAME connection check
                postgresql_connected = self.check_postgresql_connection()
                if postgresql_connected:
                    input_str={'Database': {'Connection': 'Alive'}}
                    start_response(OK_200, CONTENT_TYPE_JSON)
                    return self.format_json(input_str)
                else:
                    input_str={'Database': {'Connection': 'Error'}}
                    start_response(BAD_REQUEST_400, CONTENT_TYPE_JSON)
                    return self.format_json(input_str)

            # Fetch all routes for OOI UI App; identify static routes;
            # determine the execution time for all static routes.
            # Store result(s) in psql database; one record per route exercised.
            # Returns: JSON
            elif param_dict[KEY_SERVICE] == FETCH_STATS:

                # Check required configuration parameters are not empty
                if not self.routes_port or not self.routes_url or not self.routes_command:
                    input_str={'ERROR': 'routes_port, routes_url and routes_command must not be empty ; check config values'}
                    start_response(BAD_REQUEST_400, CONTENT_TYPE_JSON)
                    return self.format_json(input_str)

                # Get timestamp for this scenario (or group) of status checks for routes
                import datetime as dt
                scenario_timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # get all routes from OOI UI App
                try:
                    result = self.get_routes()
                    if not result:
                        input_str={'ERROR': 'no routes returned; check config values for routes_*'}
                        start_response(BAD_REQUEST_400, CONTENT_TYPE_JSON)
                        return self.format_json(input_str)
                except Exception, err:
                    start_response(BAD_REQUEST_400, CONTENT_TYPE_JSON)
                    return self.format_json(err.message)

                # execute static routes and return all execution status dictionaries in
                # list 'statuses'
                statuses = []
                if result:
                    try:
                        statuses = self.get_statuses(result)
                    except Exception, err:
                        start_response(BAD_REQUEST_400, CONTENT_TYPE_JSON)
                        return self.format_json(err.message)

                    # verify postgresql connection available; if not return error
                    if not (self.check_postgresql_connection()):
                        input_str={'ERROR': 'postgres connection error; check config for postgres settings'}
                        start_response(BAD_REQUEST_400, CONTENT_TYPE_JSON)
                        return self.format_json(input_str)

                    #  write to db - use contents of statuses and timestamp to; successful psql_result == None
                    psql_result = self.postgresql_write_stats(scenario_timestamp, statuses)
                    if psql_result:
                        input_str={'ERROR': 'error writing to database \'' + self.postgresql_database + '\': ' + psql_result}
                        start_response(BAD_REQUEST_400, CONTENT_TYPE_JSON)
                        return self.format_json(input_str)

                    # response dictionary (final_results) contains 'timestamp' and 'stats'; stats is list of
                    # status results for all routes processed.
                    final_result = {}
                    #final_result['timestamp'] = scenario_timestamp      # timestamp (of fetchstats request)
                    final_result['stats']      = statuses                # list of status(es)

                    # prepare and return successful response
                    start_response(OK_200, CONTENT_TYPE_JSON)
                    return self.format_json(final_result)

            # Specified service is not valid
            # Returns: html
            else:
                input_str={'ERROR': 'Specified service parameter is incorrect or unknown; Request: ' + request }
                start_response(BAD_REQUEST_400, CONTENT_TYPE_JSON)
                return self.format_json(input_str)

        else:
            input_str='{Request: ' + request + '}{Response: ' + output + '}'
            start_response(OK_200, CONTENT_TYPE_TEXT)
            return self.format_json(input_str)

    def format_json(self, input_str=None):
        """
        Formats input; returns JSON
        :param input_str:
        :return:
        """
        io = StringIO()
        json.dump(input_str, io)
        return io.getvalue()

    def get_postgres_connection(self):
        """
        :return:
        """
        try:
            conn = psycopg2.connect(
                database=self.postgresql_database,
                user=self.postgresql_username,
                password=self.postgresql_password,
                host=self.postgresql_host,
                port=self.postgresql_port)
            return conn
        except psycopg2.DatabaseError, err:
            return err

    def check_postgresql_connection(self):
        """
        :return:
        """
        conn = self.get_postgres_connection()
        if type(conn) == psycopg2.OperationalError:
            return None
        else:
            return conn.status

    def postgresql_write_stats(self, ts, stats):
        '''
        for each stat in stats, write performance status information to database
        '''
        conn = None
        try:
            conn = self.get_postgres_connection()
            c = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            for s in stats:
                r = s['status']
                query = 'insert into performance_stats(timestamp, status_code, url_processed, timespan, route_url, route_endpoint) ' + \
                    'values(\'%s\', \'%s\', \'%s\', %s, \'%s\', \'%s\' );' % \
                    (ts, r['status_code'], r['url_processed'], str(r['timespan']), r['route_url'], r['route_endpoint'] )
                c.execute(query)
                conn.commit()
            return None
        except Exception, err:
            return err.message
        except psycopg2.DatabaseError, err:
            return err.message
        finally:
            if conn:
                if type(conn) != psycopg2.OperationalError:
                    conn.close()

    def get_routes(self):
        '''
        Get list of (route, endpoint) tuples from OOI UI App (see value of route_command in config)
        On error return input_str dictionary with ERROR.
        '''
        # Prepare url for fetching list of (route, endpoints) tuples
        actual_route_url = 'http://' + self.routes_url + ':' + str(self.routes_port) + self.routes_command
        result = None
        try:
            list_result = requests.get(actual_route_url,timeout=(self.routes_timeout_connect, self.routes_timeout_read))
            if list_result:
                if list_result.status_code == 200:
                    if list_result.json():
                        result = list_result.json()
        except Exception, err:
            input_str={'ERROR': 'failed to retrieve routes; verify OOI UI services are runnning and value of config setting \'routes_command\'.'}
            raise Exception(input_str)

        return result

    def get_statuses(self, result):
        '''
        Determine static vs. dynamic routes. For all 'static' routes, execute url and
        get elapsed time for request-response; returns response result (as json) and status dictionary.
        Return all status dictionaries gathered in list 'statuses'
        Each status dictionary contains: status_code, timespan, route_url;
        route_url, route_endpoint and url_processed added
        '''
        routes = result['routes']
        static_routes, dynamic_routes = self.separate_routes(routes)
        statuses = []
        try:
            base_url = 'http://' + self.routes_url + ':' + str(self.routes_port)
            for static_tuple in static_routes:
                sr = static_tuple[0]
                se = static_tuple[1]
                actual_route_url = base_url  + sr
                try:
                    status = self.url_get_status(actual_route_url)
                    status['status']['route_url'] = sr
                    status['status']['route_endpoint'] = se
                    status['status']['url_processed'] = actual_route_url
                except Exception, err:
                    print 'WARNING: exception while processing route: %s, error: %s' % (sr, err)
                    print 'WARNING: exception status: %s' % status

                if status:
                    statuses.append(status)

        except Exception, err:
            input_str={'ERROR': 'exception while processing static route: ' + sr + ' error: ' + err.message}
            raise Exception(input_str)

        return statuses

    def separate_routes(self, routes):
        '''
        for all routes, separate into static and dynamic route lists
        '''
        dynamic_routes = []
        static_routes = []
        for res in routes:
            route = res[0]
            endpoint = res[1]
            if "<" in route:
                dynamic_routes.append((route, endpoint))
            else:
                if route not in static_routes:
                    static_routes.append((route, endpoint))

        return static_routes, dynamic_routes

    def url_get_status(self, query_string):
        '''
        Get status result by processing a single query string.
        Determine execution time (in seconds), return status dictionary containing:
           status_code, timespan (execution time for request-response in seconds)
        '''
        result_str={'status': {'timespan': '', 'status_code': ''}}
        try:
            if not query_string: raise Exception('ERROR : query_string parameter is empty')
            import datetime as dt
            start_time = dt.datetime.now()
            result = requests.get(query_string,timeout=(self.routes_timeout_connect, self.routes_timeout_read))
            end_time = dt.datetime.now()
            delta = end_time-start_time
            timespan       = delta.total_seconds()
            status_code    = result.status_code
            result_str['status']['timespan']    = timespan
            result_str['status']['status_code'] = status_code
            return result_str
        except Exception, err:
            result_str = {}

        return result_str

    # required
    def load_config(self):
        config = dict([(key, value) for key, value in iteritems(self.options)
                       if key in self.cfg.settings and value is not None])
        for key, value in iteritems(config):
            self.cfg.set(key.lower(), value)

    # required
    def load(self):
        return self.application

def handler_app_original(environ, start_response):
        response_body = b'Works fine...'
        status = '200 OK'
        response_headers = [
            ('Content-Type', 'text/plain'),
        ]
        start_response(status, response_headers)
        return [response_body]

def number_of_workers():
    return (multiprocessing.cpu_count() * 2) + 1

if __name__ == '__main__':
    options = {
        'bind': '%s:%s' % ('127.0.0.1', '8000'),
        'workers': number_of_workers(),
    }
    StatusHandler(handler_app_original, options).run()


