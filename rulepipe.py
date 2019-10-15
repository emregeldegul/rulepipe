import os
import json
import logging
from redis import Redis
from db_mongo import Mongo
from db_local import LocalDB
from dotenv import load_dotenv

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
    def __init__(self):
        logging.info('Rule manager initializing')
        logging.debug('Database client initializing')
        self.init_database_client()
        
        if(os.getenv("use_caching") == "True" or os.getenv("use_caching") == "true"):
            self.init_redis_client()

    def init_database_client(self):
        """
        Initializes a Rule Management with specified database.

        By default, local (and in-memory) dictionary object is used as a DB.
        In "local" db, it will not be persistent.
        """
        db              = os.getenv("db_type")
        db_ip           = os.getenv("db_server")
        db_port         = os.getenv("db_port")
        db_user         = os.getenv("db_user")
        db_pass         = os.getenv("db_pass")
        db_name         = os.getenv("db_name")
        db_authenticate = os.getenv("db_authenticate")
        
        if db == "local":
            logging.info("Database type: In-memory database")
            self.db = LocalDB()
        elif db == "mongo" or db == "mongodb":
            logging.info("Database type: MongoDB.")
            if(db_authenticate == 'True' or db_authenticate == 'true' or db_authenticate == '1'):
                self.db = Mongo(ip=db_ip, port=db_port, username=db_user, password=db_pass, auth=True, db_name=db_name)
            else:
                self.db = Mongo(ip=db_ip, port=db_port, db_name=db_name)
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
        return self.execute_rule_json(name, json.loads(data_string))

    def execute_rule_json(self, name, data):
        """
        Runs rule using given data and returns the result
        """
        if(os.getenv("use_caching") == 'True' or os.getenv("use_caching") == 'true'):
            return self.execute_rule_json_with_caching(name, data)
        else:
            return self.execute_rule_json_without_caching(name, data)


    def execute_rule_json_with_caching(self, name, data):
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

    def execute_rule_json_without_caching(self, name, data):
        flow = self.db.get_flow(name)
        response = self.process_steps(flow, data)
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

    rules = RuleManager()
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
                        "field": "statusCode",
                        "condition": "gte",
                        "value": 200
                    }
                ]
            }
        ]
    }
    """)

    rules.execute_rule_json_as_string("guray2", """
    {
        "responseTimeInSeconds": 10,
        "statusCode": 201
    }
    """)
