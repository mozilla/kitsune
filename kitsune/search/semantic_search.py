"""
E5 Multilingual Semantic Search Functions

This module provides semantic search capabilities using Elasticsearch's E5 multilingual model.
Includes both pure semantic search and hybrid (semantic + traditional text) search functions
for all SUMO document types.

Functions support all 76 SUMO locales through the E5 multilingual model's native
cross-language understanding capabilities.
"""

from elasticsearch.dsl import Q as DSLQ

from kitsune.search.documents import ForumDocument, ProfileDocument, QuestionDocument, WikiDocument


def _build_semantic_query(semantic_field, query_text, locale='en-US'):
    """
    Build a semantic query for the specified field and locale.

    Args:
        semantic_field (str): The semantic field name (e.g., 'content_semantic')
        query_text (str): The search query text
        locale (str): The locale code (defaults to 'en-US')

    Returns:
        elasticsearch.dsl.Q: Semantic query object
    """
    field_name = f"{semantic_field}.{locale}"
    return DSLQ('semantic', field=field_name, query=query_text)


def _build_text_query(text_fields, query_text, locale='en-US'):
    """
    Build a traditional text query across multiple fields for the specified locale.

    Args:
        text_fields (list): List of text field names
        query_text (str): The search query text
        locale (str): The locale code (defaults to 'en-US')

    Returns:
        elasticsearch.dsl.Q: Text query object
    """
    localized_fields = [f"{field}.{locale}" for field in text_fields]
    return DSLQ('multi_match', query=query_text, fields=localized_fields, type='best_fields')


# =============================================================================
# WIKI DOCUMENT SEARCH FUNCTIONS
# =============================================================================

def semantic_search_wiki(query_text, locale='en-US', size=10):
    """
    Pure E5 semantic search on wiki documents.

    Searches across title_semantic, content_semantic, summary_semantic, and
    keywords_semantic fields for comprehensive semantic matching.

    Args:
        query_text (str): The search query text
        locale (str): The locale code (defaults to 'en-US')
        size (int): Number of results to return (defaults to 10)

    Returns:
        elasticsearch.dsl.Search: Search object ready for execution
    """
    search = WikiDocument.search()

    # Build semantic queries for all wiki semantic fields
    title_query = _build_semantic_query('title_semantic', query_text, locale)
    content_query = _build_semantic_query('content_semantic', query_text, locale)
    summary_query = _build_semantic_query('summary_semantic', query_text, locale)
    keywords_query = _build_semantic_query('keywords_semantic', query_text, locale)

    # Combine semantic queries with field importance boosting
    combined_query = (
        title_query | content_query | summary_query | keywords_query
    )

    return search.query(combined_query).extra(size=size)


def hybrid_search_wiki(query_text, locale='en-US', size=10, semantic_weight=0.6):
    """
    Hybrid search combining E5 semantic and traditional text search on wiki documents.

    Args:
        query_text (str): The search query text
        locale (str): The locale code (defaults to 'en-US')
        size (int): Number of results to return (defaults to 10)
        semantic_weight (float): Weight for semantic results (0.0-1.0, defaults to 0.6)

    Returns:
        elasticsearch.dsl.Search: Search object ready for execution
    """
    search = WikiDocument.search()

    # Semantic component
    semantic_query = (
        _build_semantic_query('title_semantic', query_text, locale) |
        _build_semantic_query('content_semantic', query_text, locale) |
        _build_semantic_query('summary_semantic', query_text, locale) |
        _build_semantic_query('keywords_semantic', query_text, locale)
    )

    # Text component
    text_query = _build_text_query(
        ['title', 'content', 'summary', 'keywords'],
        query_text,
        locale
    )

    # Combine with weights
    text_weight = 1.0 - semantic_weight
    combined_query = DSLQ('bool', should=[
        DSLQ('constant_score', filter=semantic_query, boost=semantic_weight),
        DSLQ('constant_score', filter=text_query, boost=text_weight)
    ])

    return search.query(combined_query).extra(size=size)


# =============================================================================
# QUESTION DOCUMENT SEARCH FUNCTIONS
# =============================================================================

def semantic_search_questions(query_text, locale='en-US', size=10):
    """
    Pure E5 semantic search on question documents.

    Searches across question_title_semantic, question_content_semantic, and
    answer_content_semantic fields.

    Args:
        query_text (str): The search query text
        locale (str): The locale code (defaults to 'en-US')
        size (int): Number of results to return (defaults to 10)

    Returns:
        elasticsearch.dsl.Search: Search object ready for execution
    """
    search = QuestionDocument.search()

    # Build semantic queries for question fields
    title_query = _build_semantic_query('question_title_semantic', query_text, locale)
    content_query = _build_semantic_query('question_content_semantic', query_text, locale)
    answer_query = _build_semantic_query('answer_content_semantic', query_text, locale)

    combined_query = title_query | content_query | answer_query

    return search.query(combined_query).extra(size=size)


def hybrid_search_questions(query_text, locale='en-US', size=10, semantic_weight=0.6):
    """
    Hybrid search combining E5 semantic and traditional text search on question documents.

    Args:
        query_text (str): The search query text
        locale (str): The locale code (defaults to 'en-US')
        size (int): Number of results to return (defaults to 10)
        semantic_weight (float): Weight for semantic results (0.0-1.0, defaults to 0.6)

    Returns:
        elasticsearch.dsl.Search: Search object ready for execution
    """
    search = QuestionDocument.search()

    # Semantic component
    semantic_query = (
        _build_semantic_query('question_title_semantic', query_text, locale) |
        _build_semantic_query('question_content_semantic', query_text, locale) |
        _build_semantic_query('answer_content_semantic', query_text, locale)
    )

    # Text component
    text_query = _build_text_query(
        ['question_title', 'question_content', 'answer_content'],
        query_text,
        locale
    )

    # Combine with weights
    text_weight = 1.0 - semantic_weight
    combined_query = DSLQ('bool', should=[
        DSLQ('constant_score', filter=semantic_query, boost=semantic_weight),
        DSLQ('constant_score', filter=text_query, boost=text_weight)
    ])

    return search.query(combined_query).extra(size=size)


# =============================================================================
# ANSWER DOCUMENT SEARCH FUNCTIONS
# =============================================================================

def semantic_search_answers(query_text, locale='en-US', size=10):
    """
    Pure E5 semantic search on answer documents.

    Note: AnswerDocument inherits from QuestionDocument, so it has the same semantic fields.
    This function specifically targets answer content.

    Args:
        query_text (str): The search query text
        locale (str): The locale code (defaults to 'en-US')
        size (int): Number of results to return (defaults to 10)

    Returns:
        elasticsearch.dsl.Search: Search object ready for execution
    """
    search = QuestionDocument.search()

    # Focus on answer content semantic field and filter for actual answers
    answer_query = _build_semantic_query('content_semantic', query_text, locale)

    # Filter to only return answer documents (not question documents)
    return search.query(answer_query).filter('exists', field='content_semantic').extra(size=size)


def hybrid_search_answers(query_text, locale='en-US', size=10, semantic_weight=0.6):
    """
    Hybrid search combining E5 semantic and traditional text search on answer documents.

    Args:
        query_text (str): The search query text
        locale (str): The locale code (defaults to 'en-US')
        size (int): Number of results to return (defaults to 10)
        semantic_weight (float): Weight for semantic results (0.0-1.0, defaults to 0.6)

    Returns:
        elasticsearch.dsl.Search: Search object ready for execution
    """
    search = QuestionDocument.search()

    # Semantic component - focus on answer content
    semantic_query = _build_semantic_query('content_semantic', query_text, locale)

    # Text component - focus on answer content
    text_query = _build_text_query(['answer_content'], query_text, locale)

    # Combine with weights
    text_weight = 1.0 - semantic_weight
    combined_query = DSLQ('bool', should=[
        DSLQ('constant_score', filter=semantic_query, boost=semantic_weight),
        DSLQ('constant_score', filter=text_query, boost=text_weight)
    ])

    # Filter to only return answer documents
    return search.query(combined_query).filter('exists', field='content_semantic').extra(size=size)


# =============================================================================
# PROFILE DOCUMENT SEARCH FUNCTIONS
# =============================================================================

def semantic_search_profiles(query_text, size=10):
    """
    Pure E5 semantic search on user profile documents.

    Note: ProfileDocument uses regular SemanticTextField (not locale-aware) since
    user names are typically not localized.

    Args:
        query_text (str): The search query text
        size (int): Number of results to return (defaults to 10)

    Returns:
        elasticsearch.dsl.Search: Search object ready for execution
    """
    search = ProfileDocument.search()

    # Profile name semantic search (no locale specification needed)
    name_query = DSLQ('semantic', field='name_semantic', query=query_text)

    return search.query(name_query).extra(size=size)


def hybrid_search_profiles(query_text, size=10, semantic_weight=0.6):
    """
    Hybrid search combining E5 semantic and traditional text search on profile documents.

    Args:
        query_text (str): The search query text
        size (int): Number of results to return (defaults to 10)
        semantic_weight (float): Weight for semantic results (0.0-1.0, defaults to 0.6)

    Returns:
        elasticsearch.dsl.Search: Search object ready for execution
    """
    search = ProfileDocument.search()

    # Semantic component
    semantic_query = DSLQ('semantic', field='name_semantic', query=query_text)

    # Text component (assuming there's a 'name' text field)
    text_query = DSLQ('match', name=query_text)

    # Combine with weights
    text_weight = 1.0 - semantic_weight
    combined_query = DSLQ('bool', should=[
        DSLQ('constant_score', filter=semantic_query, boost=semantic_weight),
        DSLQ('constant_score', filter=text_query, boost=text_weight)
    ])

    return search.query(combined_query).extra(size=size)


# =============================================================================
# FORUM DOCUMENT SEARCH FUNCTIONS
# =============================================================================

def semantic_search_forums(query_text, size=10):
    """
    Pure E5 semantic search on forum documents.

    Note: ForumDocument uses regular SemanticTextField (not locale-aware).

    Args:
        query_text (str): The search query text
        size (int): Number of results to return (defaults to 10)

    Returns:
        elasticsearch.dsl.Search: Search object ready for execution
    """
    search = ForumDocument.search()

    # Build semantic queries for forum fields
    title_query = DSLQ('semantic', field='thread_title_semantic', query=query_text)
    content_query = DSLQ('semantic', field='content_semantic', query=query_text)

    combined_query = title_query | content_query

    return search.query(combined_query).extra(size=size)


def hybrid_search_forums(query_text, size=10, semantic_weight=0.6):
    """
    Hybrid search combining E5 semantic and traditional text search on forum documents.

    Args:
        query_text (str): The search query text
        size (int): Number of results to return (defaults to 10)
        semantic_weight (float): Weight for semantic results (0.0-1.0, defaults to 0.6)

    Returns:
        elasticsearch.dsl.Search: Search object ready for execution
    """
    search = ForumDocument.search()

    # Semantic component
    semantic_query = (
        DSLQ('semantic', field='thread_title_semantic', query=query_text) |
        DSLQ('semantic', field='content_semantic', query=query_text)
    )

    # Text component (assuming there are 'thread_title' and 'content' text fields)
    text_query = DSLQ('multi_match',
                     query=query_text,
                     fields=['thread_title', 'content'],
                     type='best_fields')

    # Combine with weights
    text_weight = 1.0 - semantic_weight
    combined_query = DSLQ('bool', should=[
        DSLQ('constant_score', filter=semantic_query, boost=semantic_weight),
        DSLQ('constant_score', filter=text_query, boost=text_weight)
    ])

    return search.query(combined_query).extra(size=size)


# =============================================================================
# CROSS-CONTENT SEARCH FUNCTIONS
# =============================================================================

def semantic_search_all_content(query_text, locale='en-US', size=10):
    """
    E5 semantic search across all content types.

    Returns results from Wiki, Questions, Answers, Profiles, and Forums
    in a single unified result set with cross-language capabilities.

    Args:
        query_text (str): The search query text
        locale (str): The locale code (defaults to 'en-US')
        size (int): Number of results to return per content type (defaults to 10)

    Returns:
        dict: Dictionary with keys 'wiki', 'questions', 'answers', 'profiles', 'forums'
              containing Search objects ready for execution
    """
    return {
        'wiki': semantic_search_wiki(query_text, locale, size),
        'questions': semantic_search_questions(query_text, locale, size),
        'answers': semantic_search_answers(query_text, locale, size),
        'profiles': semantic_search_profiles(query_text, size),
        'forums': semantic_search_forums(query_text, size)
    }


def hybrid_search_all_content(query_text, locale='en-US', size=10, semantic_weight=0.6):
    """
    Hybrid semantic + text search across all content types.

    Returns results from Wiki, Questions, Answers, Profiles, and Forums
    using hybrid search with configurable semantic weighting.

    Args:
        query_text (str): The search query text
        locale (str): The locale code (defaults to 'en-US')
        size (int): Number of results to return per content type (defaults to 10)
        semantic_weight (float): Weight for semantic results (0.0-1.0, defaults to 0.6)

    Returns:
        dict: Dictionary with keys 'wiki', 'questions', 'answers', 'profiles', 'forums'
              containing Search objects ready for execution
    """
    return {
        'wiki': hybrid_search_wiki(query_text, locale, size, semantic_weight),
        'questions': hybrid_search_questions(query_text, locale, size, semantic_weight),
        'answers': hybrid_search_answers(query_text, locale, size, semantic_weight),
        'profiles': hybrid_search_profiles(query_text, size, semantic_weight),
        'forums': hybrid_search_forums(query_text, size, semantic_weight)
    }


# =============================================================================
# ADVANCED SEARCH UTILITIES
# =============================================================================

def cross_language_semantic_search(query_text, target_locales=None, content_type='wiki', size=10):
    """
    Cross-language semantic search using E5's multilingual capabilities.

    Search in one language and find relevant content in other languages.
    Perfect for SUMO's multilingual support needs.

    Args:
        query_text (str): The search query text (in any supported language)
        target_locales (list): List of locale codes to search in (defaults to top 10 SUMO locales)
        content_type (str): Type of content to search ('wiki', 'questions', 'answers', defaults to 'wiki')
        size (int): Number of results to return per locale (defaults to 10)

    Returns:
        dict: Dictionary with locale codes as keys, containing search results
    """
    if target_locales is None:
        # Default to top SUMO locales
        target_locales = ['en-US', 'es', 'pt-BR', 'de', 'fr', 'ja', 'zh-CN', 'ru', 'pl', 'it']

    results = {}

    for locale in target_locales:
        if content_type == 'wiki':
            results[locale] = semantic_search_wiki(query_text, locale, size)
        elif content_type == 'questions':
            results[locale] = semantic_search_questions(query_text, locale, size)
        elif content_type == 'answers':
            results[locale] = semantic_search_answers(query_text, locale, size)
        else:
            raise ValueError(f"Unsupported content_type: {content_type}")

    return results


def semantic_search_with_filters(query_text, locale='en-US', content_type='wiki',
                                filters=None, size=10):
    """
    Semantic search with additional Elasticsearch filters.

    Allows combining E5 semantic search with traditional filters like date ranges,
    categories, product IDs, etc.

    Args:
        query_text (str): The search query text
        locale (str): The locale code (defaults to 'en-US')
        content_type (str): Type of content to search ('wiki', 'questions', 'answers')
        filters (dict): Dictionary of filters to apply (e.g., {'category': 'troubleshooting'})
        size (int): Number of results to return (defaults to 10)

    Returns:
        elasticsearch.dsl.Search: Search object with semantic query and filters applied
    """
    # Get base semantic search
    if content_type == 'wiki':
        search = semantic_search_wiki(query_text, locale, size)
    elif content_type == 'questions':
        search = semantic_search_questions(query_text, locale, size)
    elif content_type == 'answers':
        search = semantic_search_answers(query_text, locale, size)
    else:
        raise ValueError(f"Unsupported content_type: {content_type}")

    # Apply additional filters
    if filters:
        for field, value in filters.items():
            if isinstance(value, list):
                search = search.filter('terms', **{field: value})
            else:
                search = search.filter('term', **{field: value})

    return search


# =============================================================================
# EXAMPLE USAGE AND TESTING FUNCTIONS
# =============================================================================

def test_semantic_search_examples():
    """
    Example usage of E5 multilingual semantic search functions.

    This function demonstrates how to use various semantic search functions
    and can be used for testing E5 functionality.
    """
    # Basic semantic search examples
    print("=== Basic Semantic Search Examples ===")

    # Wiki semantic search
    wiki_results = semantic_search_wiki("Firefox crashes when opening", locale='en-US', size=5)
    print(f"Wiki semantic search: {len(list(wiki_results.execute()))} results")

    # Question semantic search
    question_results = semantic_search_questions("browser freezing", locale='en-US', size=5)
    print(f"Question semantic search: {len(list(question_results.execute()))} results")

    # Hybrid search examples
    print("\n=== Hybrid Search Examples ===")

    # Wiki hybrid search with different semantic weights
    hybrid_light = hybrid_search_wiki("slow performance", semantic_weight=0.3, size=5)
    hybrid_heavy = hybrid_search_wiki("slow performance", semantic_weight=0.8, size=5)
    print(f"Hybrid search (30% semantic): {len(list(hybrid_light.execute()))} results")
    print(f"Hybrid search (80% semantic): {len(list(hybrid_heavy.execute()))} results")

    # Cross-language search examples
    print("\n=== Cross-Language Search Examples ===")

    # Search in Spanish, find results in multiple languages
    cross_lang_results = cross_language_semantic_search(
        "problemas de rendimiento del navegador",  # Spanish: "browser performance problems"
        target_locales=['en-US', 'es', 'fr'],
        content_type='wiki',
        size=3
    )
    for locale, results in cross_lang_results.items():
        print(f"Cross-language results for {locale}: {len(list(results.execute()))} results")

    # Comprehensive search across all content types
    print("\n=== All Content Types Search ===")

    all_content = semantic_search_all_content("installation problems", size=3)
    for content_type, results in all_content.items():
        try:
            count = len(list(results.execute()))
            print(f"{content_type.capitalize()}: {count} results")
        except Exception as e:
            print(f"{content_type.capitalize()}: Error - {e}")
