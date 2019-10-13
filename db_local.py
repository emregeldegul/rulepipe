import logging
class LocalDB:
    def __init__(self):
        self.db = {}

    def add_rule(self, name, rule):
        if not name in self.db.keys():
            self.db[name] = []
        self.db[name].append(rule)

    def get_flow(self, name):
        if not name in self.db.keys():
            logging.error("Rule not found.")
            return
        return self.db[name]