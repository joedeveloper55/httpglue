# API Documentation

These docs give you the details of the various classes and exceptions that make up the httpglue api. Take a look at the [The official httpglue wsgi exemplar project]() and [The official httpglue asgi exemplar project]() if you'd prefer to just see some examples. 

## Intro

Excluding the small handful of framework defined exceptions, httpglue has only 5 classes to know: 
* httpglue.Request - an object that represents an http request
* httpglue.Response - an object that represents an http response
* httpglue.Headers - an object representing the http headers in a request or response 
* httpglue.WsgiApp - an object representing your application. It's where you define the code that responds to http requests from clients. It is a valid wsgi application runnable in any [pep-3333](https://peps.python.org/pep-3333/) compliant wsgi server.
* httpglue.AsgiApp - an object representing your application. It's where you define the code that responds to http requests from clients. It is a valid asgi application runnable in any [asgi spec](https://asgi.readthedocs.io/en/latest/index.html)) compliant asgi server.

## httpglue.Request

## httpglue.Response

## httpglue.Headers

## httpglue.WsgiApp

## httpglue.AsgiApp

## httpglue.* (exceptions)
