from kitsune.groups.tests import EnterpriseCompanyFactory
from kitsune.products.models import SupportContract
from kitsune.products.tests import (
    ProductFactory,
    SupportContractFactory,
    SupportCoverageFactory,
    TopicFactory,
)
from kitsune.products.utils import (
    get_products,
    get_support_locale,
    get_taxonomy,
)
from kitsune.sumo.tests import TestCase


class GetTaxonomyTests(TestCase):
    def setUp(self):
        p1 = ProductFactory(title="product1", slug="p1")
        p2 = ProductFactory(title="product2", slug="p2")
        self.p3 = p3 = ProductFactory(title="product3", slug="mozilla-account", visible=False)
        p4 = ProductFactory(title="product4", slug="p4", visible=False)
        p5 = ProductFactory(title="product5", slug="p5", is_archived=True)

        TopicFactory(
            title="topic1",
            description="Something brief about t1...",
            metadata={
                "description": "Details about t1...",
                "example-questions-assigned-to-this-topic": [
                    "Can you tell me about topic1?",
                    "Is there a setting for topic1?",
                ],
            },
            products=[p1, p2, p3, p4],
        )
        t2 = TopicFactory(
            title="topic2",
            description="Something brief about t2...",
            metadata={
                "description": "Details about t2...",
                "example-questions-assigned-to-this-topic": [
                    "Can you tell me about topic2?",
                    "Is there a setting for topic2?",
                ],
            },
            products=[p2, p3, p4],
        )
        t3 = TopicFactory(
            title="topic3",
            description="Something brief about t3...",
            metadata={"description": "Details about t3..."},
            products=[p2, p3, p4],
        )
        TopicFactory(
            title="topic4",
            description="Something brief about t4...",
            metadata={
                "description": "Details about t4...",
                "example-questions-assigned-to-this-topic": [
                    "Can you tell me about topic4?",
                    "Is there a setting for topic4?",
                ],
            },
            parent=t2,
            products=[p2, p3, p4],
        )
        t5 = TopicFactory(
            title="topic5",
            description="Something brief about t5...",
            metadata={},
            parent=t3,
            products=[p2, p3, p4],
        )
        t6 = TopicFactory(
            title="topic6",
            description="Something brief about t6...",
            metadata={
                "description": "Details about t6...",
                "example-questions-assigned-to-this-topic": [
                    "Can you tell me about topic6?",
                    "Is there a setting for topic6?",
                ],
            },
            parent=t3,
            products=[p3, p4],
        )
        TopicFactory(
            title="topic7",
            description="Something brief about t7...",
            metadata={"description": "Details about t7..."},
            parent=t5,
            products=[p2, p3, p4],
        )
        TopicFactory(
            title="topic8",
            description="Something brief about t8...",
            metadata={},
            parent=t6,
            products=[p3, p4],
        )
        TopicFactory(
            title="topic9",
            description="Something brief about t9...",
            metadata={
                "description": "Details about t9...",
                "example-questions-assigned-to-this-topic": [
                    "Can you tell me about topic9?",
                    "Is there a setting for topic9?",
                ],
            },
            parent=t6,
            products=[p3, p4],
        )
        TopicFactory(
            title="topic10",
            description="Something brief about t10...",
            metadata={"description": "Details about t10..."},
            products=[p4, p5],
        )

    def test_all_products_with_defaults(self):
        self.assertEqual(
            get_taxonomy(),
            """topics:
- title: topic1
  description: Something brief about t1...
  products:
  - title: product1
  - title: product2
  - title: product3
  subtopics: []
- title: topic2
  description: Something brief about t2...
  products:
  - title: product2
  - title: product3
  subtopics:
  - title: topic4
    description: Something brief about t4...
    products:
    - title: product2
    - title: product3
    subtopics: []
- title: topic3
  description: Something brief about t3...
  products:
  - title: product2
  - title: product3
  subtopics:
  - title: topic5
    description: Something brief about t5...
    products:
    - title: product2
    - title: product3
    subtopics:
    - title: topic7
      description: Something brief about t7...
      products:
      - title: product2
      - title: product3
      subtopics: []
  - title: topic6
    description: Something brief about t6...
    products:
    - title: product3
    subtopics:
    - title: topic8
      description: Something brief about t8...
      products:
      - title: product3
      subtopics: []
    - title: topic9
      description: Something brief about t9...
      products:
      - title: product3
      subtopics: []
""",
        )

    def test_all_products_as_json(self):
        self.assertEqual(
            get_taxonomy(output_format="json"),
            """{
  "topics": [
    {
      "title": "topic1",
      "description": "Something brief about t1...",
      "products": [
        {
          "title": "product1"
        },
        {
          "title": "product2"
        },
        {
          "title": "product3"
        }
      ],
      "subtopics": []
    },
    {
      "title": "topic2",
      "description": "Something brief about t2...",
      "products": [
        {
          "title": "product2"
        },
        {
          "title": "product3"
        }
      ],
      "subtopics": [
        {
          "title": "topic4",
          "description": "Something brief about t4...",
          "products": [
            {
              "title": "product2"
            },
            {
              "title": "product3"
            }
          ],
          "subtopics": []
        }
      ]
    },
    {
      "title": "topic3",
      "description": "Something brief about t3...",
      "products": [
        {
          "title": "product2"
        },
        {
          "title": "product3"
        }
      ],
      "subtopics": [
        {
          "title": "topic5",
          "description": "Something brief about t5...",
          "products": [
            {
              "title": "product2"
            },
            {
              "title": "product3"
            }
          ],
          "subtopics": [
            {
              "title": "topic7",
              "description": "Something brief about t7...",
              "products": [
                {
                  "title": "product2"
                },
                {
                  "title": "product3"
                }
              ],
              "subtopics": []
            }
          ]
        },
        {
          "title": "topic6",
          "description": "Something brief about t6...",
          "products": [
            {
              "title": "product3"
            }
          ],
          "subtopics": [
            {
              "title": "topic8",
              "description": "Something brief about t8...",
              "products": [
                {
                  "title": "product3"
                }
              ],
              "subtopics": []
            },
            {
              "title": "topic9",
              "description": "Something brief about t9...",
              "products": [
                {
                  "title": "product3"
                }
              ],
              "subtopics": []
            }
          ]
        }
      ]
    }
  ]
}""",
        )

    def test_all_products_with_metadata(self):
        self.assertEqual(
            get_taxonomy(
                include_metadata=["description", "example-questions-assigned-to-this-topic"]
            ),
            """topics:
- title: topic1
  description: Details about t1...
  example-questions-assigned-to-this-topic:
  - Can you tell me about topic1?
  - Is there a setting for topic1?
  products:
  - title: product1
  - title: product2
  - title: product3
  subtopics: []
- title: topic2
  description: Details about t2...
  example-questions-assigned-to-this-topic:
  - Can you tell me about topic2?
  - Is there a setting for topic2?
  products:
  - title: product2
  - title: product3
  subtopics:
  - title: topic4
    description: Details about t4...
    example-questions-assigned-to-this-topic:
    - Can you tell me about topic4?
    - Is there a setting for topic4?
    products:
    - title: product2
    - title: product3
    subtopics: []
- title: topic3
  description: Details about t3...
  products:
  - title: product2
  - title: product3
  subtopics:
  - title: topic6
    description: Details about t6...
    example-questions-assigned-to-this-topic:
    - Can you tell me about topic6?
    - Is there a setting for topic6?
    products:
    - title: product3
    subtopics:
    - title: topic9
      description: Details about t9...
      example-questions-assigned-to-this-topic:
      - Can you tell me about topic9?
      - Is there a setting for topic9?
      products:
      - title: product3
      subtopics: []
""",
        )

    def test_specific_product_with_metadata(self):
        expected = """topics:
- title: topic1
  description: Details about t1...
  example-questions-assigned-to-this-topic:
  - Can you tell me about topic1?
  - Is there a setting for topic1?
  subtopics: []
- title: topic2
  description: Details about t2...
  example-questions-assigned-to-this-topic:
  - Can you tell me about topic2?
  - Is there a setting for topic2?
  subtopics:
  - title: topic4
    description: Details about t4...
    example-questions-assigned-to-this-topic:
    - Can you tell me about topic4?
    - Is there a setting for topic4?
    subtopics: []
- title: topic3
  description: Details about t3...
  subtopics:
  - title: topic6
    description: Details about t6...
    example-questions-assigned-to-this-topic:
    - Can you tell me about topic6?
    - Is there a setting for topic6?
    subtopics:
    - title: topic9
      description: Details about t9...
      example-questions-assigned-to-this-topic:
      - Can you tell me about topic9?
      - Is there a setting for topic9?
      subtopics: []
"""
        self.assertEqual(
            get_taxonomy(
                self.p3,
                include_metadata=["description", "example-questions-assigned-to-this-topic"],
            ),
            expected,
        )
        self.assertEqual(
            get_taxonomy(
                "mozilla-account",
                include_metadata=["description", "example-questions-assigned-to-this-topic"],
            ),
            expected,
        )
        self.assertEqual(
            get_taxonomy(
                "product3",
                include_metadata=["description", "example-questions-assigned-to-this-topic"],
            ),
            expected,
        )


class GetProductsTests(TestCase):
    def setUp(self):
        ProductFactory(
            title="product1",
            description="All about product1...",
            metadata={
                "description": "Detailed description of product1...",
            },
            display_order=1,
            slug="p1",
        )
        ProductFactory(
            title="product2",
            description="All about product2...",
            metadata={
                "description": "Detailed description of product2...",
            },
            display_order=2,
            slug="p2",
        )
        ProductFactory(
            title="product3",
            description="All about product3...",
            metadata={
                "description": "Detailed description of product3...",
            },
            display_order=3,
            slug="mozilla-account",
            visible=False,
        )
        ProductFactory(
            title="product4",
            description="All about product4...",
            metadata={
                "description": "Detailed description of product4...",
            },
            display_order=4,
            slug="p4",
            visible=False,
        )
        ProductFactory(
            title="product5",
            description="All about product5...",
            metadata={
                "description": "Detailed description of product5...",
            },
            display_order=5,
            slug="p5",
            is_archived=True,
        )

    def test_get_products(self):
        expected = """products:
- title: product1
  description: All about product1...
- title: product2
  description: All about product2...
- title: product3
  description: All about product3...
"""
        self.assertEqual(get_products(), expected)

    def test_get_products_as_json(self):
        expected = """{
  "products": [
    {
      "title": "product1",
      "description": "All about product1..."
    },
    {
      "title": "product2",
      "description": "All about product2..."
    },
    {
      "title": "product3",
      "description": "All about product3..."
    }
  ]
}"""
        self.assertEqual(get_products(output_format="JSON"), expected)

    def test_get_products_with_metadata(self):
        expected = """products:
- title: product1
  description: Detailed description of product1...
- title: product2
  description: Detailed description of product2...
- title: product3
  description: Detailed description of product3...
"""
        self.assertEqual(get_products(include_metadata=["description"]), expected)

    def test_get_products_with_metadata_as_json(self):
        expected = """{
  "products": [
    {
      "title": "product1",
      "description": "Detailed description of product1..."
    },
    {
      "title": "product2",
      "description": "Detailed description of product2..."
    },
    {
      "title": "product3",
      "description": "Detailed description of product3..."
    }
  ]
}"""
        self.assertEqual(
            get_products(include_metadata=["description"], output_format="JSON"), expected
        )


class GetSupportLocaleTests(TestCase):
    def setUp(self):
        self.company = EnterpriseCompanyFactory()

    def add_contract(self, languages, **kwargs):
        contract = SupportContractFactory(company=self.company, languages=languages, **kwargs)
        SupportCoverageFactory(contract=contract)

    def assert_locales(self, expected_by_locale):
        for locale, expected in expected_by_locale.items():
            with self.subTest(locale=locale):
                self.assertEqual(get_support_locale(self.company, locale), expected)

    def test_without_a_contract_in_effect_the_locale_is_kept(self):
        self.add_contract(["de"], status=SupportContract.Status.CANCELLED)
        SupportCoverageFactory(contract__languages=["fr"])
        self.assert_locales({"it": "it", "": "en-US"})

    def test_the_one_extra_language_is_the_default(self):
        self.add_contract(["de"])
        self.assert_locales({"de": "de", "en-US": "en-US", "it": "de", "": "de"})

    def test_several_languages_across_contracts_default_to_english(self):
        self.add_contract(["de"])
        self.add_contract(["fr"])
        self.assert_locales({"de": "de", "fr": "fr", "it": "en-US", "": "en-US"})

    def test_a_contract_without_extra_languages_defaults_to_english(self):
        self.add_contract([])
        self.assert_locales({"en-US": "en-US", "it": "en-US", "": "en-US"})
