import os
import time
import json
import logging
import hashlib
from redis import Redis
from .interfaces.mongodb import Mongo
from .interfaces.localdb import LocalDB
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
        "all": lambda args: all(args),
        "fromfile": lambda d,fname: RuleOperations.fromfile(d, fname)
        }

    files = {}

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
    
    @staticmethod
    def fromfile(d, fname):
        print(d, fname)
        if not fname in RuleOperations.files.keys():
            hashes = []
            for line in open(fname, 'r').readlines():
                hashes.append((line.strip().split(':')[0]))

            RuleOperations.files[fname] = hashes
            print(list(RuleOperations.files[fname]))
        
        print(RuleOperations.files[fname])

        return d in RuleOperations.files[fname]




class RuleManager(object):
    def __init__(self):
        logging.info('Rule manager initializing')
        logging.debug('Database client initializing')
        self.load_environment_variables()
        self.init_database_client()
        
        if(self.ENV["USE_CACHE"]):
            logging.info("Caching active")
            self.init_redis_client(self.ENV["REDIS_IP"], self.ENV["REDIS_PORT"])

    def load_environment_variables(self):
        self.load_dotenv_if_defined()
        self.ENV = {
            "DB_TYPE"         : str(os.getenv("RULEPIPE_DB_TYPE", "local")).lower(),
            "DB_IP"           : os.getenv("RULEPIPE_DB_IP", "127.0.0.1"),
            "DB_PORT"         : int(os.getenv("RULEPIPE_DB_PORT", 27017)),
            "DB_USER"         : os.getenv("RULEPIPE_DB_USER", "rulepipe"),
            "DB_PASSWORD"     : os.getenv("RULEPIPE_DB_PASSWORD", ""),
            "DB_NAME"         : os.getenv("RULEPIPE_DB_NAME", "rulepipe"),
            "DB_AUTHENTICATE" : json.loads(os.getenv("RULEPIPE_DB_AUTHENTICATE", "False").lower()),
            "USE_CACHE"       : json.loads(os.getenv("RULEPIPE_USE_CACHE", "False").lower()),
            "REDIS_IP"        : os.getenv("RULEPIPE_REDIS_IP", "127.0.0.1"),
            "REDIS_PORT"      : int(os.getenv("RULEPIPE_REDIS_PORT", 6379))
        }

    def load_dotenv_if_defined(self):
        env_file = os.getenv("RULEPIPE_ENVFILE")
        if(env_file):
            logging.info("Using Environment File : " + str(env_file))
            load_dotenv(env_file)
        else:
            logging.info("Environment file not specified. Looking for in-folder .env file")
            load_dotenv()

    def init_database_client(self):
        """
        Initializes a Rule Management with specified database.

        By default, local (and in-memory) dictionary object is used as a DB.
        In "local" db, it will not be persistent.
        """

        if self.ENV["DB_TYPE"] == "local":
            logging.info("Database type: In-memory database")
            self.db = LocalDB()
        elif self.ENV["DB_TYPE"] == "mongo" or self.ENV["DB_TYPE"] == "mongodb":
            logging.info("Database type: MongoDB.")
            if self.ENV["DB_AUTHENTICATE"]:
                self.db = Mongo(
                    ip      =self.ENV["DB_IP"], 
                    port    =self.ENV["DB_PORT"], 
                    username=self.ENV["DB_USER"], 
                    password=self.ENV["DB_PASSWORD"], 
                    auth    =True, 
                    db_name =self.ENV["DB_NAME"]
                )
            else:
                self.db = Mongo(
                    ip     =self.ENV["DB_IP"], 
                    port   =self.ENV["DB_PORT"], 
                    db_name=self.ENV["DB_NAME"]
                )
        else:
            logging.error("This database type is not supporting.")

    def init_redis_client(self, host, port):
        self.redis = Redis(host, port)

    def add_rule_json_as_string(self, name, rule_string):
        """
        Adds a JSON formatted string rule into Rule Database as JSON
        """
        return self.add_rule_json(name, json.loads(rule_string))

    def add_rule_json(self, name, rule):
        """
        Adds a rule into Rule Database as JSON
        """

        if 'type' not in rule:
            error_message = "At least one 'type' value required to add new rule."
            logging.error(error_message)
            raise KeyError(error_message)

        is_added_to_database = self.db.add_rule(name, rule)

        if is_added_to_database and self.ENV["USE_CACHE"]:
            logging.debug("New rule caching...")
            rule_name_hash = self.md5(name)
            rule_time_hash = self.md5(name + "_cache_time")
            self.redis.set(rule_name_hash, str(rule))
            self.redis.set(rule_time_hash, str(time.time()))
        return True

    def delete_rule(self, name):
        if self.ENV["USE_CACHE"]:
            rule_name_hash = self.md5(name)
            rule_time_hash = self.md5(name + "_cache_time")
            self.redis.delete(rule_name_hash, rule_time_hash)
        return self.db.delete_rule(name)

    def execute_rule_json_as_string(self, name, data_string):
        """
        Runs a JSON formatted rule string and returns the result
        """
        return self.execute_rule_json(name, Data(json.loads(data_string)))

    def execute_rule_json(self, name, data):
        """
        Runs rule using given data and returns the result
        """
        if self.ENV["USE_CACHE"] and not self.redis == None:
            logging.debug("Checking is Redis connected : " + str(self.redis.ping()))
            return self.execute_rule_json_with_caching(name, data)
        else:
            return self.execute_rule_json_without_caching(name, data)

    def md5(self, text):
        return hashlib.md5(str(text).encode()).hexdigest()

    def is_cached_statement_updated(self, rule_time_hash, statement_time_hash):
        rule_time = self.redis.get(rule_time_hash)
        statement_time = self.redis.get(statement_time_hash)

        if(
            rule_time      == None or rule_time      == b'None' or 
            statement_time == None or statement_time == b'None'
        ):
            return True
        return float(rule_time) > float(statement_time)

    def execute_rule_json_with_caching(self, name, data):
        rule_name_hash = self.md5(name)
        rule_time_hash = self.md5(name + "_cache_time")
        statement_name_hash = self.md5(name + "_" + str(data))
        statement_time_hash = self.md5(statement_name_hash + "_cache_time")

        logging.debug("Checking Rule flow existance in cache with { rule_name_hash: " + rule_name_hash + " , rule_time_hash: " + rule_time_hash + " }")
        
        if (
            self.redis.get(rule_name_hash) == b'None' or 
            self.redis.get(rule_name_hash) ==   None  or 
            self.redis.get(rule_time_hash) == b'None' or
            self.redis.get(rule_time_hash) ==   None
        ):
            logging.debug("Rule flow not found in cache, fetching from db...")
            flow_db_record = self.db.get_flow(name)
            if flow_db_record:
                logging.debug("Rule fetched from db, caching...")
                self.redis.set(rule_name_hash, str(flow_db_record))
                self.redis.set(rule_time_hash, str(time.time()))
            else:
                logging.error("Rule couldnt fetch from db.")
                return

        logging.debug("Rule flow found in cache, fetching...")
        flow = [json.loads(str(self.redis.get(rule_name_hash), 'utf-8').replace("\'", "\""))]
        logging.debug("Rule Flow: " + str(flow.__class__) + " : " + str(flow))

        logging.debug("Checking Statement result existance in cache with { statement_name_hash: " + statement_name_hash + " , statement_time_hash: " + statement_time_hash + " }")
        if(
            self.redis.get(statement_name_hash) == b'None' or self.redis.get(statement_name_hash) == None or
            self.is_cached_statement_updated(rule_time_hash, statement_time_hash)):
            logging.debug("rule_time : " + str(self.redis.get(rule_time_hash)) + ", statement_time : " + str(self.redis.get(statement_time_hash)) + "\n")
            logging.debug("Statement not found or become old in cache , executing...")
            response = self.process_steps(flow, data)
            logging.debug("Statement execute completed. Caching...")
            self.redis.set(statement_name_hash, str(response))
            self.redis.set(statement_time_hash, str(time.time()))
        else:
            logging.debug("Statement found in cache, fetching...")
            response = str(self.redis.get(statement_name_hash), 'utf-8')
            logging.debug("Statement: " + str(response))

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

    def get_rule_list(self):
        """
        Returns saved rules list.
        """
        return list(self.db.get_rules())

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
        for rule in step["rules"]:
            results.append(RuleOperations.eval(rule, data))
        return RuleOperations.operations[step["match"]](results)

    def process_steps(self, flow, data):
        if(flow):
            for step in flow:
                logging.debug("Processing Step: " +  str(step))

                if step["type"] == "rule":
                    result = self.processRule(step, data)
                    logging.debug("Result: " + str(result))
                    return result

                elif step["type"] == "ruleset":
                    logging.debug("RuleSet found, continuing recursively.")
                    rulesetResults = []
                    for rule in step["rules"]:
                        logging.debug("Rule sent #149:" + str(rule) + str(type(rule)))
                        rulesetResults.append(self.process_steps([rule], data))
                    return RuleOperations.operations[step["match"]](rulesetResults)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    rules = RuleManager()
    
    print(rules.get_rule_list())

    rules.add_rule_json_as_string("guray6", """
    {
        "type": "ruleset",
        "match": "all",
        "rules": [
            {
                "type": "rule",
                "match": "all",
                "rules": [
                    {
                        "field": "responseTimeInSeconds",
                        "condition": "lte",
                        "value": 0.45
                    },
                    {
                        "field": "statusCode",
                        "condition": "gte",
                        "value": 200
                    }
                ]
            },
            {
                "type": "rule",
                "match": "any",
                "rules": [
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
    

    print(rules.execute_rule_json_as_string("guray6", """
    {
        "responseTimeInSeconds": 0.1,
        "statusCode": 200,
        "details": {
            "name": "mymetric",
            "importance": 7
        }
    }
    """))


    print(rules.get_rule_list())

    print(rules.delete_rule("guray6"))
    print(rules.delete_rule("guray6"))

    print(rules.get_rule_list())
