## Omega 365 client service

A microservice for connecting to Omega 365.

[![SesamCommunity CI&CD](https://github.com/sesam-community/omega365/actions/workflows/sesam-community-ci-cd.yml/badge.svg)](https://github.com/sesam-community/omega365/actions/workflows/sesam-community-ci-cd.yml)

### Environment variables

**Important!** user/password authentication is no longer supported by Omega. Replaced by ApiKey authentication.
As of v1.7 only ApiKey authentication is supported in this microservice.

`base_url` - base url to the Omega 365 instance.

`API_KEY` - Omega 365 ApiKey used for authentication (supplied by Omega).

`resources` - a list of the configured Omega 365 API endpoints, the following properties are declarable for each endpoint:

`LOG_LEVEL` - Defaults to "INFO".

* fields: a list of the properties exposed by the endpoint. Required property.
* viewName: name of the Omega 365 resource. Required property.
* id_property_name: name of the property containing the unique id of an entity. Required property.
* since_property_name: name of the property containing the value for the since marker if the resource supports since functionality for continuation support. Optional property.

### Example system config

```json
{
  "_id": "omega365-system",
  "type": "system:microservice",
  "docker": {
    "environment": {
      "API_KEY": "$SECRET(omega365-apikey)",
      "base_url": "$ENV(omega365-url)",
      "LOG_LEVEL": "DEBUG",
      "page_number": "1",
      "page_size": "1000",
      "protocol": "json",
      "resources": [{
        "fields": [{
          "name": "PrimKey"
        }, {
          "name": "Created"
        }, {
          "name": "Name"
        }],
        "id_property_name": "PrimKey",
        "viewName": "omega365-integration-resourcename",
        "since_property_name": "Updated"
      }]
    },
    "image": "sesamcommunity/omega365:1.7",
    "port": 5002
  }
}
```

### Example pipe config when used as a source

```json
{
  "_id": "omega365-pipe",
  "type": "pipe",
  "source": {
    "type": "json",
    "system": "omega365-system",
    "completeness": false,
    "is_since_comparable": true,
    "supports_since": true,
    "url": "omega365-integration-resourcename"
  }
}
```

### Example pipe config when used as a sink

```json
{
  "_id": "omega365-endpoint",
  "type": "pipe",
  "source": {
    "type": "dataset",
    "dataset": "omega365-dataset"
  },
  "sink": {
    "type": "json",
    "system": "omega365-system",
    "url": "omega365-integration-resourcename"
  }
}

```