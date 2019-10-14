# rulepipe

The rule engine you always deserved.

RulePipe is a declarative, scalable, highly configurable rule engine. Usage areas include, but not limited to;

- Classification
- Filtering
- Triggering other tasks
- User-driven flow implementations
- Event based checks
- Domain specific complex rule inputs

## Installation

RulePipe uses no external Python package as a module. But, to use RulePipe
as a service with REST API, install flask package. RulePipe is written in
Python3.

### Pre-installation

Please install the necessary packages.

```sh
~$ pip install -r requirements.txt
```

And rename the .env.example file to .env.

```sh
~$ mv .env.example .env
```

Then we make the database settings in the .env file.

### Run RulePipe REST API Service

- Clone this repository `git clone https://git.ray.kim/guray/rulepipe.git`
- Change directory to repository directory `cd rulepipe`
- Run flask service `export FLASK_APP=api.py && python3 -m flask run`

Is enough for installing and using RulePile as a RESTful service.

### Test the Service

If you have successfully installed and runned RulePipe, now you can use it as a
rule engine service.

To add a simple rule to your engine:

~~~sh
curl --header "Content-Type: application/json" --request POST --data '
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
  }
  ' http://localhost:5000/add_rule/myNewRule
~~~

In this rule screnario, if `"responseTimeInSeconds"` value is less than or
equal to 3.45 and `"statusCode"` value is greater than or equal to 200 ,
input statement going to return `True` else return `False`.
(because `"Match"` is `"all"`, it returns `True` if all the conditions are `True`)

When you run make this request, if everything is OK, result is `"OK"`.

---

To check a simple statement:

~~~sh
curl --header "Content-Type: application/json" --request POST --data '
  {
    "responseTimeInSeconds": 2,
    "statusCode": 200
  }
  ' http://localhost:5000/execute_rule/myNewRule
~~~

This statement is provides the conditions of our rule, so its result should be:
`{"response":true}` with `200` return code.

If we check another statement as below:

~~~sh
curl --header "Content-Type: application/json" --request POST --data '
  {
    "responseTimeInSeconds": 5,
    "statusCode": 404
  }
  ' http://localhost:5000/execute_rule/myNewRule
~~~

Although 404 is greather than 200, because of 5 is greater than 3.45
our condition is not providing the condition of our rule. So its result should
be as:
`{"response":false}` with `200` return code.

## RoadMap

- [x] Add REST API
- [ ] Support subfields in JSON (probably needs dot notation)
- [ ] Support nested rules
- [ ] Read database information from config file and environment variables
- [x] Add persistent DB (maybe MongoDB)
- [x] Add cache for rules (maybe Redis)
- [x] Add cache for statement return values
- [ ] Support defining custom conditions
- [ ] Support predefined actions
- [ ] Support defining custom actions
- [ ] Set hash of data as Redis keys
- [x] Add webhooks for Telegram to track progress
- [ ] Support for OpenTracing
- [ ] Add logging and use log levels
