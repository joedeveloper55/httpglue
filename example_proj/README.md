# HTTP Glue Simple Sample Project

This project exists to showcase how a small json http microservice can be built with httpglue.

It has the idiomatic code structure of an httpglue app, so is a good example for how to organize your code.

This sample is intended to be ran on a multi-threaded wsgi server and leverages a single backing service (Postgres).

The sample comes with a full suite of unit tests, which showcase the idiomatic way to unit test apps built with httpglue (however, If you'd like to use test doubles and mocks a lot less (i.e using a real database locally) we don't see that as a bad thing. Such tests have many advantages over more isolated unit testing. Do not take all the test doubles here as us implying that httpglue apps should be tested in this fashion in all circumstances and teams).

This example project is a great place to get started with learning httpglue because there are so few other technolgies you need to know to understand it. Also, it shows just how well httpglue can *scale down* to small projects and simple tasks.

## setting up your virtual env and getting dependencies

> python3 -m venv env
> . ./env/bin/activate
> pip install -r requirements.txt

## running the test code for the project

> PYTHONPATH=. python -m unittest discover tests

## deploying/running the project

\* note: I leave installing postgressql up to you if you want to locally deploy this,
   since there are multiple ways to do this and it will depend on your machine, OS,
   and environment

> PGSQL_DSN=$YOUR_PGSQL_DSN PYTHONPATH=. waitress-serve --host 127.0.0.1 --call app:make_app 