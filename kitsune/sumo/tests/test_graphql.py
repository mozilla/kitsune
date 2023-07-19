from graphene_django.utils.testing import GraphQLTestCase

from kitsune.users.tests import GroupFactory, UserFactory


class GraphQLTestCases(GraphQLTestCase):
    def test_graphql_anonymous(self):
        response = self.query(
            """
            query {
                currentUser {
                    email
                }
            }
            """
        )
        self.assertResponseNoErrors(response)
        self.assertEqual(response.json(), {"data": {"currentUser": None}})

    def test_graphql_authenticated(self):
        user = UserFactory()
        self.client.login(username=user.username, password="testpass")
        response = self.query(
            """
            query {
                currentUser {
                    id
                    email
                    username
                    isContributor
                }
            }
            """
        )
        self.assertResponseNoErrors(response)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "currentUser": {
                        "id": str(user.id),
                        "email": user.email,
                        "username": user.username,
                        "isContributor": False,
                    }
                }
            },
        )

    def test_graphql_authenticated_contributor(self):
        user = UserFactory(groups=[GroupFactory(name="l10n-contributors")])
        self.client.login(username=user.username, password="testpass")
        response = self.query(
            """
            query {
                currentUser {
                    isContributor
                }
            }
            """
        )
        self.assertResponseNoErrors(response)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "currentUser": {
                        "isContributor": True,
                    }
                }
            },
        )

    def test_graphql_introspection(self):
        query = """
            query {
                __schema {
                    types {
                        name
                        description
                    }
                }
            }
        """
        user = UserFactory()
        self.client.login(username=user.username, password="testpass")
        response = self.query(query)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("errors", data)
        self.assertEqual(len(data["errors"]), 1)
        self.assertIn("message", data["errors"][0])
        self.assertEqual(data["errors"][0]["message"], "GraphQL introspection is disabled.")
        self.assertIn("data", data)
        self.assertIs(data["data"], None)
