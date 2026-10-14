def decision_answers(probability=0.1, relevance_uncertainty=0.1):
    return {
        "spam": {"type": "predicate", "name": "spam", "probability": probability},
        "relevance_uncertainty": {
            "type": "predicate",
            "name": "relevance_uncertainty",
            "probability": relevance_uncertainty,
        },
    }


def choice_answer(name, value, probability=0.99):
    return {
        name: {
            "type": "choice",
            "name": name,
            "choice": value,
            "probabilities": [{"value": value, "probability": probability}],
            "confidence": 0.01,
        }
    }
