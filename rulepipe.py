import os
import json
import logging
from redis import Redis
from db_mongo import Mongo
from db_local import LocalDB
from dotenv import load_dotenv

class Data(dict):
    def __getitem__(self, name):
        print("__getitem__ called for {}".format(name))
        fields = name.split('.')
        c = self
        for field in fields:
            print(c, field)
            c = dict.__getitem__(c, field)
        return c

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
        logging.debug("Evauluating: " + str(data))
        return RuleOperations.get_operation(
                rule["condition"],
                data[rule["field"]],
                rule["value"]
                )

    @staticmethod
    def get_operation(condition, data, value):
        logging.debug("Condition: {}, Data: {}, Value: {}".format(
            condition, data, value))
        logging.debug(RuleOperations.operations[condition](data, value))
        return RuleOperations.operations[condition](data, value)


class RuleManager(object):
    def __init__(self, db='local', db_address='', db_name='rulepipe'):
        logging.info('Rule manager initializing')
        logging.debug('Database client initializing')
        self.init_database_client(db, db_address, db_name)
        self.init_redis_client()

    def init_database_client(self, db, db_address, db_name):
        """
        Initializes a Rule Management with specified database.

        By default, local (and in-memory) dictionary object is used as a DB.
        In "local" db, it will not be persistent.
        """
        if db == "local":
            logging.info("Database type: In-memory database")
            self.db = LocalDB()
        elif db == "mongo" or db == "mongodb":
            logging.info("Database type: MongoDB.")
            self.db = Mongo()
        else:
            logging.error("This database type is not supporting.")

    def init_redis_client(self, host="localhost", port=6379):
        self.redis = Redis(host, port)

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

    def execute_rule_json_as_string(self, name, data_string):
        """
        Runs a JSON formatted rule string and returns the result
        """
        return self.execute_rule_json(name, Data(json.loads(data_string)))

    def execute_rule_json(self, name, data):
        """
        Runs rule using given data and returns the result
        """
        rule_key = name + "_" + str(data)
        if(self.redis.get(rule_key) == None):
            logging.debug("Statement not found in cache, executing...")
            if(self.redis.get(name) == None):
                logging.debug("Rule flow not found in cache, fetching from db...")
                flow = self.db.get_flow(name)
                logging.debug("Rule fetched, caching...")
                self.redis.set(name, str(flow))
            else:
                logging.debug("Rule flow found in cache, fetching...")
                flow = json.loads(str(self.redis.get(name), 'utf-8').replace("\'", "\""))
            response = self.process_steps(flow, data)
            logging.debug("Statement execute completed. Caching...")
            self.redis.set(rule_key, str(response))
        else:
            logging.debug("Statement found in cache, fetching...")
            response = str(self.redis.get(rule_key), 'utf-8')
        return response

    def add_rule_code(self, name, rule):
        """
        Adds a rule into Rule Database as code.

        DANGER: Be really careful if you are planning to use this.
        May be INSECURE.
        """
        logging.critical("This function is not activated yet: add_rule_code")
        self.add_rule_json(name, rule)

    def execute_rule_code(self, name, data):
        """
        Runs rule using given data and returns the result

        DANGER: Be really careful if you are planning to use this.
        May be INSECURE.
        """
        logging.critical("This function is not activated yet: execute_rule_code")
        pass

    def processRule(self, step, data):
        results = []
        for rule in step["Rules"]:
            results.append(RuleOperations.eval(rule, data))
        return RuleOperations.operations[step["Match"]](results)

    def process_steps(self, flow, data):
        for step in flow:
            logging.debug("Processing Step: " +  str(step))

            if step["Type"] == "rule":
                result = self.processRule(step, data)
                logging.debug("Result: " + str(result))
                return result

            elif step["Type"] == "ruleset":
                logging.debug("RuleSet found, continuing recursively.")
                rulesetResults = []
                for rule in step["Rules"]:
                    logging.debug("Rule sent #149:" + str(rule) + str(type(rule)))
                    rulesetResults.append(self.process_steps([rule], data))
                return RuleOperations.operations[step["Match"]](rulesetResults)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    load_dotenv()

    db_ip = os.getenv("mdb_server")
    db_port = os.getenv("mdb_port")
    db_user = os.getenv("mdb_user")
    db_pass = os.getenv("mdb_pass")
    #db_connect_url = "mongodb://" + db_user + ":" + db_pass + "@" + db_ip + ":" + str(db_port)
    db_connect_url = "mongodb://localhost:27017/"

    rules = RuleManager(db="local", db_address=db_connect_url)
    rules.add_rule_json_as_string("guray2", """
    {
        "Type": "ruleset",
        "Match": "all",
        "Rules": [
            {
                "Type": "rule",
                "Match": "all",
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
            },
            {
                "Type": "rule",
                "Match": "any",
                "Rules": [
                    {
                        "field": "responseTimeInSeconds",
                        "condition": "lte",
                        "value": 3.45
                    },
                    {
                        "field": "details.importance",
                        "condition": "gte",
                        "value": 5
                    }
                ]
            }
        ]
    }
    """)

    rules.execute_rule_json_as_string("guray2", """
    {
        "responseTimeInSeconds": 10,
        "statusCode": 201,
        "details": {
            "name": "mymetric",
            "importance": 7
        }
    }
    """)
