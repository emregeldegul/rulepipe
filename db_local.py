import logging
class LocalDB:
    def __init__(self):
        self.db = {}

    def add_rule(self, name, rule):
        if name in self.db.keys():
            error_message = "Couldn't create new rule, rule named by {0} already exists.".format(name)
            logging.error(error_message)
            raise NameError(error_message)
        
        self.db[name] = []
        self.db[name].append(rule)

        return True

    def get_flow(self, name):
        if not name in self.db.keys():
            error_message = "Rule '{0}' not found.".format(name)
            logging.error(error_message)
            raise KeyError(error_message)

        return self.db[name]