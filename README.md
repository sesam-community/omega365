## Omega 365 client service

A rest microservice for connecting to Omega 365.

[![SesamCommunity CI&CD](https://github.com/sesam-community/omega365/actions/workflows/sesam-community-ci-cd.yml/badge.svg)](https://github.com/sesam-community/omega365/actions/workflows/sesam-community-ci-cd.yml)

### Environment variables:

`base_url` - the base url of Omega 365.

`username` - username to Omega 365.

`password` - password to Omega 365.


### Example system config:

```json
{
  "_id": "omega365-system",
  "type": "system:microservice",
  "docker": {
    "environment": {
      "base_url": "https://my.omega365.com",
      "username": "omega365-username",
      "password": "$SECRET(omega365-password)",
      "page_number": "1",
      "page_size": "1000",
      "protocol": "json"
    },
    "image": "sesamcommunity/omega365:1.0",
    "port": 5002
  }
}

```

```