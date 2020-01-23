from falcon import testing
import unittest.main
from app import api


class MyTestCase(testing.TestCase):
    def setUp(self):
        super(MyTestCase, self).setUp()
        self.app = api


class TestRulepipe(MyTestCase):
    def test_1_rule_list(self):
        response = self.simulate_get("/rules")
        self.assertEqual(response.json, {"rules": []})

    def test_2_add_rule_with_missing_body(self):
        response = self.simulate_post("/add_rule/AwesomeRule", json={})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json,
            {"msg": "At least one 'type' value required to add new rule."},
        )

    def test_3_add_rule(self):
        _rule = {
            "type": "rule",
            "match": "all",
            "rules": [
                {"field": "responseTimeInSeconds", "condition": "lte", "value": 3.45},
                {"field": "statusCode", "condition": "gte", "value": 200},
            ],
        }
        response = self.simulate_post("/add_rule/AwesomeRule", json=_rule)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json, {"msg": "Rule created successfully."})

    def test_4_execute_rule(self):
        _values = {"responseTimeInSeconds": 2, "statusCode": 200}
        response = self.simulate_post("/rules/AwesomeRule", json=_values)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"msg": True})

    def test_5_delete_rule(self):
        response = self.simulate_delete("/rules/AwesomeRule")

        self.assertEqual(response.json, {"msg": True})


if __name__ == "__main__":
    unittest.main()
