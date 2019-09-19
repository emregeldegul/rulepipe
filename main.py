import json

class RuleOperations(object):

    operations = {
        "gt": lambda a,b: a > b,
        "gte": lambda a,b: a >= b,
        "lt": lambda a,b: a < b,
        "lte": lambda a,b: a <= b,
        "eq": lambda a,b: a == b,
        "ne": lambda a,b: a != b,
        "mod": lambda a,b: a % b,
        "any": lambda *args: any(args),
        "all": lambda *args: all(args)
        }

    @staticmethod
    def gt(a, b):
        return a > b

    @staticmethod
    def add(*args):
        return sum(args)

    @staticmethod
    def multiply(*args):
        result = 1
        for arg in args:
            result *= arg
        return result

    @staticmethod
    def eval(rule, data):
        print(type(rule), rule)
        print(type(data), data)
        return RuleOperations.get_operation(
                rule["condition"],
                data[rule["field"]],
                rule["value"]
                )

    @staticmethod
    def get_operation(condition, data, value):
        print("Incoming:\n\tCondition: {}\n\tData: {}\n\tValue: {}".format(
            condition, data, value
        )
        )
        print(RuleOperations.operations[condition](data, value))


class RuleManager(object):
    def __init__(self, db='local'):
        """
        Initializes a Rule Management with specified database.
        
        By default, local (and in-memory) dictionary object is used as a DB.
        In "local" db, it will not be persistent.
        """
        if db == "local":
            self._rules = {}
            self.db = self._rules

    def add_rule_json(self, name, rule):
        """
        Adds a rule into Rule Database as JSON
        """
        self.db[name] = json.loads(rule)
        print("Info about rule:", type(self.db[name][0]), self.db[name][0])

    def execute_rule_json(self, name, data):
        """
        Runs rule using given data and returns the result
        """
        if not name in self.db.keys():
            print("Rule not found.")
            return
        flow = self.db[name]
        self.processSteps(flow, data)
        # for step in flow:
        # step["Match"]

    def add_rule_code(self, name, rule):
        """
        Adds a rule into Rule Database as code.

        DANGER: Be really careful if you are planning to use this.
        May be INSECURE.
        """
        self.add_rule_json(name, rule)

    def execute_rule_code(self, name, data):
        """
        Runs rule using given data and returns the result

        DANGER: Be really careful if you are planning to use this.
        May be INSECURE.
        """
        pass

    def processRule(self, step, data):
        data = json.loads(data)
        results = []
        for rule in step["Rules"]:
            results.append(RuleOperations.eval(rule, data))
        # return getattr(RuleOperations, step["Match"])(results)
        return RuleOperations.operations[step["Match"]](results)

    def processSteps(self, flow, data):

        for step in flow:
            if step["Type"] == "rule":
                result = self.processRule(step, data)
                print("Result:", result)
        
            if step["Type"] == "ruleset":
                pass


if __name__ == "__main__":
    print("Starting to work with an in memory database...")
    rules = RuleManager()
    rules.add_rule_json("guray", """[
    {
        "Type": "rule",
        "Match": "all",
        "WhatToDo": [
            {
                "internalAction": "sendTelegramMessage"
            },
            {
                "runFunction": "myFunction"
            }
        ],
        "Rules": [
            {
                "field": "responseTimeInSeconds",
                "condition": "lte",
                "value": 3.45
            },
            {
                "field": "statusCode",
                "condition": "gte",
                "value": 200
            }
        ]
    }]""")
    rules.execute_rule_json("guray", """{
        "responseTimeInSeconds": 3,
        "statusCode": 201
    }""")
    print("Rule Manager Started")
    myRule = """{"all": {}}"""
