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


@app.route("/retrieve", methods=["POST"])
@app.route("/create", methods=["POST"])
def crud():
    request_url = "{0}{1}".format(url, "/api/data")
    logger.info("Request url: %s", request_url)

    request_data = json.loads(request.data)

    if remove_namespaces:
        for key in request_data[0]:
            if ":" in key:
                new_key = key.split(":")[1]
                request_data[0][new_key] = request_data[0].pop(key)

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
