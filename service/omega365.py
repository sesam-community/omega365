import requests
from flask import Flask, Response, request
import os
import logger
import cherrypy
import json

app = Flask(__name__)
logger = logger.Logger('Omega365 client service')

url = os.environ.get("base_url")
username = os.environ.get("username")
pw = os.environ.get("password")
remove_namespaces = os.environ.get("remove_namespaces", True)
headers = json.loads('{"Content-Type": "application/json"}')


class BasicUrlSystem:
    def __init__(self, config):
        self._config = config

    def make_session(self):
        session = requests.Session()
        session.headers = self._config["headers"]
        session.verify = True
        return session


session_factory = BasicUrlSystem({"headers": headers})


def authenticate(s):
    auth_url = url + "/login?mobile_login=true"

    auth_content = {
        "username_user": username,
        "password": pw,
        "remember": "false"
    }

    try:
        auth_resp = s.request("POST", auth_url, json=auth_content)
    except Exception as e:
        logger.warning("Exception occurred when authenticating the user: '%s'", e)


def stream_json(clean):
    first = True
    yield '['
    for i, row in enumerate(clean):
        if not first:
            yield ','
        else:
            first = False
        yield json.dumps(row)
    yield ']'


def remove_ns(keys):
    if isinstance(keys, list):
        for key in keys:
            remove_ns(key)
    if isinstance(keys, dict):
        for key in keys.keys():
            if ":" in key:
                new_key = key.split(":")[1]
                keys[new_key] = keys.pop(key)
        for val in keys.values():
            remove_ns(val)


@app.route("/retrieve", methods=["POST"])
def retrieve():
    request_url = "{0}{1}".format(url, "/api/data")
    logger.info("Request url: %s", request_url)

    request_data = json.loads(request.data)

    if remove_namespaces:
        remove_ns(request_data[0])

    logger.info("Request data: %s", request_data[0])

    with session_factory.make_session() as s:
        authenticate(s)

        response = s.request("POST", request_url, json=request_data[0], headers=headers)

        if response.status_code != 200:
            raise Exception(response.reason + ": " + response.text)

        result = json.loads(response.text)

    return Response(
            stream_json(result['success']),
            mimetype='application/json'
        )


@app.route("/create", methods=["POST"])
def create():
    request_url = "{0}{1}".format(url, "/api/data")
    logger.info("Request url: %s", request_url)

    request_data = request.get_json()

    if remove_namespaces:
        remove_ns(request_data)

    logger.info("Request data: %s", request_data)

    def generate(entities):
        yield "["
        with session_factory.make_session() as s:
            authenticate(s)
            for index, entity in enumerate(entities):
                if index > 0:
                    yield ","

                response = s.request("POST", request_url, json=entity, headers=headers)

                if response.status_code != 200:
                    logger.warning("An error occurred: {0}. {1}".format(response.reason, response.text))
                    raise Exception(response.reason + ": " + response.text)

                result = json.loads(response.text)

                yield json.dumps(result['success'])
        yield "]"

    response_data_generator = generate(request_data)
    response_data = response_data_generator
    return Response(response=response_data, mimetype="application/json")


@app.route("/delete", methods=["DELETE"])
def delete():
    request_url = "{0}{1}".format(url, "/api/data")
    logger.info("Request url: %s", request_url)

    request_data = request.get_json()

    if remove_namespaces:
        remove_ns(request_data)

    logger.info("Request data: %s", request_data)

    return None

if __name__ == '__main__':
    cherrypy.tree.graft(app, '/')

    # Set the configuration of the web server to production mode
    cherrypy.config.update({
        'environment': 'production',
        'engine.autoreload_on': False,
        'log.screen': True,
        'server.socket_port': 5002,
        'server.socket_host': '0.0.0.0'
    })

    # Start the CherryPy WSGI web server
    cherrypy.engine.start()
    cherrypy.engine.block()
