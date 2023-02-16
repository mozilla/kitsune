# 3 - AAQ structure in Search

Date: 2020-10-27

## Status

Pending

## Context

As we are re-implementing our search in ElasticSearch v7,
we must re-implement Ask a Question (AAQ) search.

There is one primary use-case for storing AAQ documents in ES which Search v1 supports,
which we must continue to be able to do in the redesigned Search:
searching for an AAQ thread as a unit.

There are other secondary use-cases which we may want to support when storing AAQ documents in ES.
A non-exhaustive list of these are:

-   Searching within AAQ threads
-   Searching within questions and their solutions
-   Aggregating answers to create contribution data

We also want search to be _fast_,
so should model our data to avoid nested fields and parent-child relationships,
and use de-normalization wherever possible:
https://www.elastic.co/guide/en/elasticsearch/reference/7.9/tune-for-search-speed.html#_document_modeling

## Decision

We will model our data in ES based on what makes most sense for our expected use-cases,
and what will make those fast and efficient,
rather than feeling like we must have a 1:1 copy of our data structure in our database.

In this vein, we will use a structure of two document "types" within one index,
`QuestionDocument` and `AnswerDocument`,
where a `QuestionDocument` will exist for each `Question` which exists in the database,
and an `AnswerDocument` will exist for each `Answer` which exists in the database.

`AnswerDocument` will be a subclass of `QuestionDocument` so will inherit all of its fields,
and we will set the value of those fields to the value of the `Question` associated with its `Answer`.

For instance, if in database:

```
answer.created => 2020-10-27
answer.question.created => 2020-11-01
```

in elastic:

```
answer_document.created => 2020-10-27
answer_document.question_created => 2020-11-01
```

`QuestionDocument` will also have an `answer_content` field,
which contains the content of all a Question's Answers.
We will set this to null in the `AnswerDocument`.

## Consequences

`QuestionDocument`s can be distinguished from `AnswerDocument`s by whether the `created` value is null or not.

This structure gives us great flexibility over the type of searches and aggregations we can do:

-   AAQ threads can be searched over as a unit by searching over the `question_content` and `answer_content` fields on a `QuestionDocument`.
    Collapsing or aggregations aren't required to ensure that threads only appear once,
    which wouldn't be the case if we didn't have an `answer_content` field.

-   Searches within AAQ threads are possible by searching over the `question_content` fields on a `QuestionDocument`,
    and the `content` fields on an `AnswerDocument`.

-   Searches can be limited to Question content and the content of Answers which are solutions by filtering by `is_solved: True`,
    and searching over `question_content` and `content` fields.

-   Aggregations on Answers,
    such as gathering contribution metrics,
    can be performed by aggregating `AnswerDocument`s.

There may be some Question data indexed in `AnswerDocument`s which we never use.
