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

- Install flask `pip3 install flask`

### Run RulePipe REST API Service

- Clone this repository `git clone https://git.ray.kim/guray/rulepipe.git`
- Change directory to repository directory `cd rulepipe`
- Run flask service `export FLASK_APP=api.py && python3 -m flask run`

Is enough for installing and using RulePile as a RESTful service.

## RoadMap

- [x] Add REST API
- [ ] Support subfields in JSON (probably needs dot notation)
- [ ] Support nested rules
- [x] Add persistent DB (maybe MongoDB)
- [ ] Add cache for rules (maybe Redis)
- [ ] Support defining custom conditions
- [ ] Support predefined actions
- [ ] Support defining custom actions
