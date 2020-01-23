import falcon
from core import RuleManager
import json

api = falcon.API()
rulemanager = RuleManager()


class HomeResource(object):
    def on_get(self, req, resp):
        resp.content_type = falcon.MEDIA_TEXT
        resp.body = "Rulepipe is alive!"


class AddRuleResource(object):
    def on_post(self, req, resp, rule_name):
        rule = req.media

        try:
            rulemanager.add_rule_json(rule_name, rule)
        except KeyError as err:
            resp.status = falcon.HTTP_422
            resp.body = json.dumps(dict(msg=err.args[0]))
            return

        resp.status = falcon.HTTP_201
        resp.body = json.dumps(dict(msg="Rule created successfully."))


class RuleResource(object):
    def on_post(self, req, resp, rule_name):
        response = rulemanager.execute_rule_json(rule_name, req.media)
        resp.body = json.dumps(dict(msg=response))

    def on_delete(self, req, resp, rule_name):
        response = rulemanager.delete_rule(rule_name)
        resp.body = json.dumps(dict(msg=response))


class RuleListResource(object):
    def on_get(self, req, resp):
        resp.body = json.dumps(dict(rules=rulemanager.get_rule_list()))


api.add_route("/", HomeResource())
api.add_route("/add_rule/{rule_name}", AddRuleResource())
api.add_route("/rules", RuleListResource())
api.add_route("/rules/{rule_name}", RuleResource())
