import logging
class LocalDB:
    def __init__(self):
        self.db = {}

    def add_rule(self, name, rule):
        if self.is_rule_avaliable(name):
            error_message = "Couldn't create new rule, rule named by {0} already exists.".format(name)
            
            logging.error(error_message)
            raise NameError(error_message)

        self.db[name] = []
        self.db[name].append(rule)

        return True

    def delete_rule(self, name):
        if not self.is_rule_avaliable(name):
            return False
        self.db.__delitem__(name)
        return True

    def is_rule_avaliable(self, name):
        return name in self.db.keys()

    def get_flow(self, name):
        if not self.is_rule_avaliable(name):
            error_message = "Rule '{0}' not found.".format(name)
            
            logging.error(error_message)
            raise KeyError(error_message)
            
        return self.db[name]

    def get_rules(self):
        return self.db.keys()