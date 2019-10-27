import logging
class LocalDB:
    def __init__(self):
        self.db = {}

    def add_rule(self, name, rule):
        if not self.is_rule_avaliable(name):
            self.db[name] = []
        self.db[name].append(rule)

    def delete_rule(self, name):
        if not self.is_rule_avaliable(name):
            return False
        self.db.__delitem__(name)
        return True

    def is_rule_avaliable(self, name):
        return name in self.db.keys()

    def get_flow(self, name):
        if not self.is_rule_avaliable(name):
            logging.error("Rule not found.")
            return
        return self.db[name]

    def get_rules(self):
        return self.db.keys()