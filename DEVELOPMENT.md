# About httpglue

httpglue is an extremely minimal framework for writing http applications (particularly, small to medium size http microservices). It is a kind of 'nanoframework' if you will.

It is built of the back of wsgi and asgi, offering application developers the choice to either make a wsgi or an asgi app.

Its goal is to be the simplest python http framework available while still being just about good enough for the building of small but real http apps. Features and conveniences have been ruthlessly cut in pursuit of this goal. Such is the path of httpglue and should be the guiding principle of contributors to this codebase.

Beyond simplicity, the second most important goal of httpglue is transparency. What the framework is doing at any time and what happens in certain cases must never be a mystery to users of httpglue. The api and framework behavior must be sufficiently small, documented, and un-abstracted such that an experiencd python developer using it can thoroughly predict and understand what is going on in their apps, and hold the whole api and request flow in their heads. The learning curve must be very small.

Keeping dependencies as minimal as is possible is also a major goal. httpglue must use only the standard library. Installation and maintainence should be completely free of pain. Maintainers must also follow [semvar](https://semver.org/) conventions with regards to versioning.

See [the design docs](https://github.com/joedeveloper55/httpglue/blob/master/DESIGN.md) for more details on the httpglue philosophy.

## src Control Repo

https://github.com/joedeveloper55/httpglue

## Distribution Repo

xxxxxxxxx

## primary shell commands for project developers

to create your isolated env:
> python3 -m venv env

to enter your env:
> . env/bin/activate

to run the unit tests:
> PYTHONPATH=. python -m unittest discover tests

to package the project:
> pip install wheel
> python setup.py sdist bdist_wheel

to upload this project to a repo
> python3 -m twine upload --repository-url $DISTRIBUTION_REPO dist/*

to leave your env (run this when done working on this project for the day):
> deactivate
