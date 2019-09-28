from flask import Flask, request
from rulepipe import *
app = Flask(__name__)
rules = RuleManager()


@app.route('/')
def root():
  return 'Rulepipe!\n'

@app.route('/add_rule/<name>', methods=['POST'])
def add_rule(name):
  rules.add_rule_json(name, request.get_json())
  return 'OK'

@app.route('/execute_rule/<name>', methods=['POST'])
def execute_rule(name):
  print(request.get_json())
  response = rules.execute_rule_json(name, request.get_json())
  return {"response": response}