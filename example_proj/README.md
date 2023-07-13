# HTTP Glue Simple Sample Project

This project exists to showcase how a small but real json http microservice can be built with httpglue.

It has the idiomatic code structure of an httpglue app as imagined by the author of the framework, and is a good example for how to organize your code.

This sample is intended to be ran on one or more multi-threaded, multi process wsgi servers and leverages a single backing service (Postgres).

The sample comes with a full suite of unit tests, which showcase the idiomatic way to unit test apps built with httpglue (however, If you'd like to use test doubles and mocks a lot less (i.e using a real database locally) we don't see that as a bad thing. Such tests have many advantages over more isolated unit testing. Do not take all the test doubles here as us implying that httpglue apps should be tested in this fashion in all circumstances and teams, and see our [asgi exemplar]() for an alternative style of testing that actually includes and uses backing services in unit tests).

## setting up your virtual env and getting dependencies
```bash
python3 -m venv env  # if you didn't do this already
. ./env/bin/activate
pip install -r requirements.txt
```
## running the test code for the project
```bash
PYTHONPATH=. python -m unittest discover tests
```
## locally deploying/running the project

\* note: We use docker here to get a postgres server up and running quickly and easily, but if you can't get docker on your machine you should be able to install/make a postgres server in another way. We'll leave that as an exercise for you if you decide to go that way.

```bash
docker run \
   --rm \
   --name testing-db \
   -p 5432:5432
   -e POSTGRES_PASSWORD=secret \
   -e POSTGRES_USER=postgres \
   -e POSTGRES_DB=postgres \
   -d \
   postgres

DSN="postgresql://postgres:secret@127.0.0.1:5432/postgres"

./init_db.sh $DSN

PGSQL_DSN=$DSN PYTHONPATH=. waitress-serve --threads 10 --host 127.0.0.1 --call app:make_app
```

Once you've dployed the app by doing the above, it should be listening at localhost:8080.

If you use Postman, we've included a Postman collection file (Widget API V1.postman_collection.json) that you can import into postman for your convenience to directly play around with this microservice on your local machine.

## Shutting down for the day when done playing with this exemplar

```bash
docker stop testing-db
deactivate
```