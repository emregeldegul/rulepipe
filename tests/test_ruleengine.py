from rulepipe import RuleManager
from pytest import raises

rule_manager = RuleManager()


def test_add_new_rule():
    response = rule_manager.add_rule_json(
        "firstRule",
        {
            "type": "rule",
            "match": "all",
            "rules": [
                {"field": "responseTimeInSeconds", "condition": "lte", "value": 3.45},
                {"field": "statusCode", "condition": "gte", "value": 200},
            ],
        },
    )

    assert response == True


def test_add_new_rule_as_string():
    response = rule_manager.add_rule_json_as_string(
        "ruleToDelete",
        """{
            "type": "rule",
            "match": "all",
            "rules": [
                {"field": "responseTimeInSeconds", "condition": "lte", "value": 3.45},
                {"field": "statusCode", "condition": "gte", "value": 200}
            ]
        }""",
    )

    assert response == True


def test_rulename_conflict_raising():
    with raises(NameError):
        rule_manager.add_rule_json(
            "firstRule",
            {
                "type": "rule",
                "match": "all",
                "rules": [
                    {
                        "field": "responseTimeInSeconds",
                        "condition": "lte",
                        "value": 3.45,
                    },
                    {"field": "statusCode", "condition": "gte", "value": 200},
                ],
            },
        )

def test_keys_required_for_new_rule():
    with raises(KeyError):
        rule_manager.add_rule_json('itWillRaise', {})

def test_list_rules():
    rules = rule_manager.get_rule_list()

    assert rules == ["firstRule", "ruleToDelete"]


def test_rule_execution():
    response = rule_manager.execute_rule_json(
        "firstRule", {"responseTimeInSeconds": 2, "statusCode": 200}
    )

    assert response == True
