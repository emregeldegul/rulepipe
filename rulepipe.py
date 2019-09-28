import json
from db_mongo import Mongo
from db_local import LocalDB

class RuleOperations(object):

    operations = {
        "gt": lambda a,b: a > b,
        "gte": lambda a,b: a >= b,
        "lt": lambda a,b: a < b,
        "lte": lambda a,b: a <= b,
        "eq": lambda a,b: a == b,
        "ne": lambda a,b: a != b,
        "mod": lambda a,b: a % b,
        "sum": lambda args: sum(args),
        "any": lambda args: any(args),
        "all": lambda args: all(args)
        }

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
        return RuleOperations.operations[condition](data, value)


class RuleManager(object):
    def __init__(self, db='local', db_address='', db_name='rulepipe'):
        """
        Initializes a Rule Management with specified database.
        
        By default, local (and in-memory) dictionary object is used as a DB.
        In "local" db, it will not be persistent.
        """
        if db == "local":
            print("Starting to work with an in memory database...")
            self.db = LocalDB()
        elif db == "mongo" or db == "mongodb":
            print("Starting to work with MongoDB. Connecting to ", 
                db_address, "-> Database Name: " , db_name)
            self.db = Mongo()
        else:
            print("This database type is not supporting.")

    def add_rule_json_as_string(self, name, rule_string):
        """
        Adds a JSON formatted string rule into Rule Database as JSON
        """
        self.add_rule_json(name, json.loads(rule_string))

    def add_rule_json(self, name, rule):
        """
        Adds a rule into Rule Database as JSON
        """
        self.db.add_rule(name, rule)
        #print("Info about rule:", type(self.db[name]), self.db[name])

    def execute_rule_json_as_string(self, name, data_string):
        """
        Runs a JSON formatted rule string and returns the result
        """
        return self.execute_rule_json(name, json.loads(data_string))

    def execute_rule_json(self, name, data):
        """
        Runs rule using given data and returns the result
        """
        flow = self.db.get_flow(name)
        return self.processSteps(flow, data)
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
        results = []
        for rule in step["Rules"]:
            results.append(RuleOperations.eval(rule, data))
        # return getattr(RuleOperations, step["Match"])(results)
        return RuleOperations.operations[step["Match"]](results)

    def processSteps(self, flow, data):
        for step in flow:
            print("step type: " , type(step), " : " ,  step)
            if step["Type"] == "rule":
                result = self.processRule(step, data)
                print("Result:", result)
                return result

            if step["Type"] == "ruleset":
                pass


if __name__ == "__main__":
    db_ip = "localhost"
    db_port = 27017
    db_user = "rulepipe"
    db_pass = "password"
    #db_connect_url = "mongodb://" + db_user + ":" + db_pass + "@" + db_ip + ":" + str(db_port)
    db_connect_url = "mongodb://localhost:27017/"
    print("Rule Manager Started")

    rules = RuleManager(db="mongo", db_address=db_connect_url)
    rules.add_rule_json_as_string("guray", """
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
    }
    """)

    rules.execute_rule_json_as_string("guray", """
    {
        "responseTimeInSeconds": 5,
        "statusCode": 201
    }
    """)
