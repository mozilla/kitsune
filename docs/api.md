---
title: API
---

SUMO has a series of API endpoints to access data.

::: contents
:::

# Locales API

> All locales supported by SUMO.
>
> **Example request**:
>
> ``` http
> GET /api/2/locales/ HTTP/1.1
> Accept: application/json
> ```
>
> **Example response**:
>
> ``` http
> HTTP/1.0 200 OK
> Vary: Accept, X-Mobile, User-Agent
> Allow: OPTIONS, GET
> X-Frame-Options: DENY
> Content-Type: application/json
>
> {
>    "vi": {
>       "name": "Vietnamese",
>       "localized_name": "Ti\u1ebfng Vi\u1ec7t",
>       "aaq_enabled": false
>    },
>    "el": {
>       "name": "Greek",
>       "localized_name": "\u0395\u03bb\u03bb\u03b7\u03bd\u03b9\u03ba\u03ac",
>       "aaq_enabled": false
>    },
>    "en-US": {
>       "name": "English",
>       "localized_name": "English",
>       "aaq_enabled": true
>    }
> }
> ```
>
> reqheader Accept
>
> :   application/json
>
> resheader Content-Type
>
> :   application/json
>
> statuscode 200
>
> :   no error
