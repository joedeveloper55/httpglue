# The Design of httpglue

httpglue has many important desing goals. Contributers should review these to understand how to contribute to httpglue and it's broader ecosystem in such a way that preserves the properties laid out in these design goals.

Users and interested parties should review these to understand how httpglue will develop in the future, and, more importantly, how it *will not* develop in the future.

These principles are the *north star* of httpglue that have guided its design and should continue to do so.

## httpglue is minimal:

The most important quality of httpglue is that it is minimal. *It is a nanoframework*. If you know well the five core objects (WsgiApp, AsgiApp, Headers, Request, and Response) and how the framework works with them, you already have complete understanding of httpglue. The semantics and usage patterns are extremely similar whether you're writing a wsgi or asgi app.

httpglue does one single thing: allowing a programmer to basically map http requests to server side code which does things and generates responses. It is *glue* between http and any other functionality you can imagine. httpglue glue does not have integration points for your favorite orm, it does not come with a static webserver, it does not have cookie handling logic, it does not support https directly, it does not come with template rendering, it does not tell you how to build your domain objects, etc. It will not ever include this functionality in to the core framework. ever.

httpglue just litens for web requests, dispatches them to some code, and offers a means of making responses.

httpglue is meant to be an api so small and flat that an experienced python programmer could learn and memorize the entire API in less then a few hours, maybe even less than an hour; This minimalism is extremely empowering to developer flexibility, creativty, and efficiency; This minimalism enables developers and architects to build an http microservice into exactly what it needs to be from the ground up, gradually adding what they need, rather than starting with something bigger and trying to chisel away at or ignore the things they don't need.

## httpglue is explicit:

httpglue places great importance on being *explicit* and avoiding *implicit* behaviors. *magic* is not appreciated in this framework. This means that the full behavior and configuration of an httpglue app written by a developer is visible directly from the code they write. It also means that a developer writing an httpglue app must think about the full behavior and configuration of their apps upfront.

There are no default config options. Looking at the code means you are seeing the full configuration of an app. The mindset here is *configuration over convention*. We get away with this because there are not many mandatory things to configure in the framework.

There are no "surprise responses", such as a 404 html page coming out of a json api because that is what some framework defaults to when a path that does not exist is requested. Users of httpglue apps write explict code for every error and situation, and understand that if they miss one the default error response configured into the app is what will be returned.

There are no surprise modifications of outgoing responses or incoming requests, such as default headers. (other than what your wsgi or asgi server is doing, and any reverse proxies are doing, of course)

explictness is considered so important in the design of httpglue that it is allowable to ocasionally even compromise simplicity and concision in pursuit of explicitness.

## httpglue is transparent:

httpglue wants it's behaviors and configuration to be highly visible. It is meant to be observable and have no surprises.

The *explicitness* design criteria play a major role in making httpglue transparent.

Logging is another main mechanisim for providing transparency into httpglue apps. Including logging was a tough choice. On one hand we didn't want the extra complexity and to force people's hand in including logging and how to do so; On the other hand, logging was simply too important to ignore. httpglue considers a developer's ability to observe their app's behaviors absolutely critical to writing good software, learning the framework, and debugging.

Additionaly, sometimes the behavior of code is not truly transparent until it's been tested. This means the ease of testing apps written in httpglue is a core design goal. The framework must enable straightforward and powerful testing.
