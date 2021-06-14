import requests
from flask import Flask, Response, request
import os
import logger
import cherrypy
import json
from datetime import datetime

app = Flask(__name__)
logger = logger.Logger('Omega365 client service')

url = os.environ.get("base_url")
username = os.environ.get("username")
pw = os.environ.get("password")
remove_namespaces = os.environ.get("remove_namespaces", True)
headers = json.loads('{"Content-Type": "application/json"}')
resources_config = json.loads(os.environ.get("resources", '[]'))

resources = {}


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


def stream_json(clean, since_property_name, id_property_name):
    first = True
    yield '['
    for i, row in enumerate(clean):
        if not first:
            yield ','
        else:
            first = False
        if since_property_name is not None:
            row["_updated"] = row[since_property_name]
        if id_property_name is not None:
            row["_id"] = str(row[id_property_name])
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


def populate_resources():
    for resource in resources_config:
        since_property_name = None
        id_property_name = None
        if "since_property_name" in resource:
            since_property_name = resource["since_property_name"]
        if "id_property_name" in resource:
            id_property_name = resource["id_property_name"]
        resources[resource["resource_name"]] = \
            {
                "fields": resource["fields"],
                "since_property_name": since_property_name,
                "id_property_name": id_property_name
            }


@app.route("/<path:path>", methods=["GET"])
def get(path):
    request_url = "{0}{1}".format(url, "/api/data")
    logger.info("Request url: %s", request_url)

    if path not in resources:
        raise Exception("Resource with name '{0}' not found!".format(path))

    where_clause = None
    if request.args.get('since') is not None and resources[path]["since_property_name"] is not None:
        logger.info("Since marker found: {0}".format(request.args.get('since')))
        since = request.args.get('since').split(".")[0]
        where_clause = "{0} >= '{1}'".format(resources[path]["since_property_name"], datetime.strptime(since, "%Y-%m-%dT%H:%M:%S"))

    get_template = {
        "maxRecords": -1,
        "operation": "retrieve",
        "resourceName": path,
        "fields": resources[path]["fields"],
        "whereClause": where_clause
    }

    logger.info("Request data: %s", get_template)

    with session_factory.make_session() as s:
        authenticate(s)

        response = s.request("POST", request_url, json=get_template, headers=headers)

        if response.status_code != 200:
            raise Exception(response.reason + ": " + response.text)

        result = json.loads(response.text)

    return Response(
        stream_json(result['success'], resources[path]["since_property_name"], resources[path]["id_property_name"]),
        mimetype='application/json'
    )


@app.route("/<path:path>", methods=["POST"])
def post(path):
    request_url = "{0}{1}".format(url, "/api/data")
    logger.info("Request url: %s", request_url)

    if path not in resources:
        raise Exception("Resource with name '{0}' not found!".format(path))

    request_data = json.loads(request.data)

    logger.info("Request data: %s", request_data)

    create_template = {
        "maxRecords": -1,
        "operation": "create",
        "resourceName": path,
        "uniqueName": path,
        "excludeFieldNames": False,
        "fields": resources[path]["fields"]
    }

    delete_template = {
        "operation": "destroy",
        "resourceName": path,
        "uniqueName": path
    }

    update_template = {
        "operation": "update",
        "resourceName": path,
        "uniqueName": path,
        "excludeFieldNames": False,
        "fields": resources[path]["fields"]
    }

    def generate(entities):
        yield "["
        with session_factory.make_session() as s:
            authenticate(s)
            for index, entity in enumerate(entities):
                if index > 0:
                    yield ","

                post_entity = entity.copy()
                if "_deleted" in entity and entity["_deleted"] is True:
                    logger.info("Deleting entity: {0}!".format(entity["_id"]))
                    post_entity.update(delete_template)
                else:
                    if resources[path]["id_property_name"] in entity:
                        logger.info("Updating entity: {0}!".format(entity["_id"]))
                        post_entity.update(update_template)
                    else:
                        logger.info("Creating entity: {0}!".format(entity["_id"]))
                        post_entity.update(create_template)

                response = s.request("POST", request_url, json=post_entity, headers=headers)

                if response.status_code != 200:
                    logger.warning("An error occurred: {0}. {1}".format(response.reason, response.text))
                    raise Exception(response.reason + ": " + response.text)

                result = json.loads(response.text)

                yield json.dumps(result['success'])
        yield "]"

    response_data_generator = generate(request_data)
    response_data = response_data_generator
    return Response(response=response_data, mimetype="application/json")


if __name__ == '__main__':
    cherrypy.tree.graft(app, '/')

    populate_resources()

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
