# HTTP Glue Simple Sample Project

This project exists to showcase how a non production protoype of a small json http microservice can be built with httpglue.

This sample is intended to be ran on a single threaded wsgi server and has no backing services (databases, other apis, message queues, etc).

This is the kind of thing someone may build in a few hours before a meeting to have real examples of endpoints in an api a team is designing, or the kind of thing that someone could build just to experiment with how they want their api to look like.

A real production http microservice should not be built like this for obvious reasons. If you're looking for such an example, check out the xxxxx sample project or the xxxxx sample project.

Nonetheless, this example project is a great place to get started with learning httpglue because there are so few other technolgies you need to know to understand it. Also, it shows just how well httpglue can *scale down* to small projects and simple tasks, along with how powerful httpglue can be for rapid prototyping

## setting up your virtual env

> python3 -m venv env
> . ./env/bin/activate

## deploying/running the project

> pip install ../dist/*.whl
> pip install gunicorn; PYTHONPATH=. gunicorn my_app:app

## running the test code for the project

> PYTHONPATH=. python -m unittest discover tests