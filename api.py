from flask import Flask, request
from rulepipe import *

db_connect_url = "mongodb://localhost:27017/"

app = Flask(__name__)
rules = RuleManager(db="mongo", db_address=db_connect_url)

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