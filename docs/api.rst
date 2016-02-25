===
API
===

SUMO has a series of API endpoints to access data.

.. contents::


Search suggest API
==================

:Endpoint:     ``/api/2/search/suggest/``
:Method:       ``GET``
:Content type: ``application/json``
:Response:     ``application/json``

The search suggest API allows you to get back kb documents and aaq
questions that match specified arguments.

Arguments can be specified in the url querystring or in the HTTP
request body.


Required arguments
------------------

+-------------------+--------+--------------------------------------------------------+
|argument           |type    |notes                                                   |
+===================+========+========================================================+
|q                  |string  |This is the text you're querying for.                   |
+-------------------+--------+--------------------------------------------------------+


Optional arguments
------------------

+-------------------+--------+--------------------------------------------------------+
|argument           |type    |notes                                                   |
+===================+========+========================================================+
|locale             |string  |default: ``settings.WIKI_DEFAULT_LANGUAGE``             |
|                   |        |                                                        |
|                   |        |The locale code to restrict results to.                 |
|                   |        |                                                        |
|                   |        |Examples:                                               |
|                   |        |                                                        |
|                   |        |* ``en-US``                                             |
|                   |        |* ``fr``                                                |
+-------------------+--------+--------------------------------------------------------+
|product            |string  |default: None                                           |
|                   |        |                                                        |
|                   |        |The product to restrict results to.                     |
|                   |        |                                                        |
|                   |        |Example:                                                |
|                   |        |                                                        |
|                   |        |* ``firefox``                                           |
+-------------------+--------+--------------------------------------------------------+
|max_documents      |integer |default: 10                                             |
|                   |        |                                                        |
|                   |        |The maximum number of documents you want back.          |
+-------------------+--------+--------------------------------------------------------+
|max_questions      |integer |default: 10                                             |
|                   |        |                                                        |
|                   |        |The maximum number of questions you want back.          |
+-------------------+--------+--------------------------------------------------------+


Responses
---------

All response bodies are in JSON.

HTTP 200: Success
~~~~~~~~~~~~~~~~~

With an HTTP 200, you'll get back a set of results in JSON.

::

   {
       "documents": [
           {
               "id": ...                  # id of kb article
               "title": ...               # title of kb article
               "url": ...                 # url of kb article
               "slug": ...                # slug of kb article
               "locale": ...              # locale of the article
               "products": ...            # list of products for the article
               "topics": ...              # list of topics for the article
               "summary": ...             # paragraph summary of kb article (plaintext)
               "html": ...                # html of the article
           }
           ...
       ],
       "questions": [
           {
               "id": ...                  # integer id of the question
               "answers": ...             # list of answer ids
               "content": ...             # content of question (in html)
               "created": ...             # datetime stamp in iso-8601 format
               "creator": ...             # JSON object describing the creator
               "involved": ...            # list of JSON objects describing everyone who
                                            participated in the question
               "is_archived": ...         # boolean for whether this question is archived
               "is_locked": ...           # boolean for whether this question is locked
               "is_solved": ...           # boolean for whether this question is solved
               "is_spam": ...             # boolean for whether this question is spam
               "is_taken": ...            # FIXME:
               "last_answer": ...         # id for the last answer
               "num_answers": ...         # total number of answers
               "locale": ...              # the locale for the question
               "metadata": ...            # metadata collected for the question
               "tags": ...                # tags for the question
               "num_votes_past_week": ... # the number of votes in the last week
               "num_votes": ...           # the total number of votes
               "product": ...             # the product
               "solution": ...            # id of answer marked as a solution if any
               "taken_until": ...         # FIXME:
               "taken_by": ...            # FIXME:
               "title": ...               # title of the question
               "topic": ...               # FIXME:
               "updated_by": ...          # FIXME:
               "updated": ...             # FIXME:
           },
           ...
       ]
   }


Examples
--------

Using curl::

    curl -X GET "http://localhost:8000/api/2/search/suggest/?q=videos"

    curl -X GET "http://localhost:8000/api/2/search/suggest/?q=videos&max_documents=3&max_questions=3"

    curl -X GET "http://localhost:8000/api/2/search/suggest/" \
         -H "Content-Type: application/json" \
         -d '
    {
       "q": "videos",
       "max_documents": 3,
       "max_questions": 0
    }'


Locales API
===========

.. http:get:: /api/2/locales/

   All locales supported by SUMO.

   **Example request**:

   .. sourcecode:: http

      GET /api/2/locales/ HTTP/1.1
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.0 200 OK
      Vary: Accept, X-Mobile, User-Agent
      Allow: OPTIONS, GET
      X-Frame-Options: DENY
      Content-Type: application/json

      {
         "vi": {
            "name": "Vietnamese",
            "localized_name": "Ti\u1ebfng Vi\u1ec7t",
            "aaq_enabled": false
         },
         "el": {
            "name": "Greek",
            "localized_name": "\u0395\u03bb\u03bb\u03b7\u03bd\u03b9\u03ba\u03ac",
            "aaq_enabled": false
         },
         "en-US": {
            "name": "English",
            "localized_name": "English",
            "aaq_enabled": true
         },
         ...
      }

   :reqheader Accept: application/json
   :resheader Content-Type: application/json
   :statuscode 200: no error
