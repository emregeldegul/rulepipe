from pymongo import MongoClient
import json
import logging
class Mongo:
    def __init__(self, ip="localhost", port=27017, username="", 
        password="", auth=False, db_name="rulepipe"):

        if auth:
            connect_url = "mongodb://" + username + ":" + password + \
                "@" + ip + ":" + str(port)
        else:
            connect_url = "mongodb://" + ip + ":" + str(port)

        self.client = MongoClient(connect_url)

        if db_name in self.client.list_database_names():
            self.db = self.client[db_name]
        else:
            logging.error(str(db_name) + " database not exists in " + str(ip))

    def add_rule(self, name, rule):
        return self.db["rules"].insert_one({"name": name, "rule": str(rule)})

    def get_flow(self, name):
        flow = []
        for item in self.db["rules"].find({"name": name}):
            flow.append(json.loads(item["rule"].replace("\'", "\"")))
        return flow

    def get_rules(self):
        return self.db.keys()