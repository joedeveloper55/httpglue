# Tips, tricks, and best practices for httpglue users

## Best practices for running in production
  * Do not enable debug level logs in production. The logs are incredibly verbose, logging all requests in full and all responses in full. This is concerning from a security perspective. Your logs will almost certainly be a goldmine of sensitive information. Additionally though, the sheer volume of logging generated when using debug level logs in production may also be a problem and stress your logging infrastructure. The debug level logs are there to help developers debug locally or in less important deployment regions, but should generally always be avoided in production. Setting your app's logging level to Info level logs will generally strike a good balance between logging enough information to provide sufficient transparency while also not overly stressing a logging infrastructure or logging to much sensitve information.

  * Know your wsgi or asgi server, or find someone who does. httpglue is the application part of either a wsgi or asgi app. A decent portion of the behavior, reliability, and performance will be dependent on the tuning/configuration of the wsgi/asgi server you're using to run it.

## using the App object's handle_req method for fluent unit tests

Both the httpglue.wsgi.App object and the httpglue.asgi.App object expose a
'handle_req' method that takes a Req object, routes it thorough your app, and
returns a Res object.

While you will seldom if ever use this directly in application code, it is the main
tool at your disposal for writing fluent and idiomatic unit tests with httpglue.

Basically, to write your unit tests, you import/construct the App object representing
your application, and then in your unit tests you construct Req objects, pass them into
this handle_req method, and then validate the returned Res object. No wsgi or asgi
setup or specific logic is required when unit testing this way. See the [an example of httpglue unit testing here](example_proj/tests/test_app.py)

## Creating a catch-all handler

While generally not useful and likely problematic for normal apps, a catch-all handler could be useful
in some  special cases, such as if you want to make your own framework using httpglue as a sort of 'base framework', or if you're building something unusual such as a http request echo service or a mock server like service.

If you want to create such a catch-all handler, write a signature like this:

## FAQs

### how do I write concurrent apps with httpglue?

https://peps.python.org/pep-3333/#thread-support

### why doesn't httpglue have feature X?

httpglue is a 'nanoframework', a framework intended to be even smaller than most popular microframeworks. Each additional feature takes it further and further away from this concept, which is the key idea that the entire framework was designed around. In this sense, each feature is as much a liability as it is an asset. The simplicity of the framework enables developer flexibility and creativity, and the chance to keep an app simple when that's all it needs to be. The simplicity of the framework enables full learning of framework behavior at a rapid pace.

Every app and team will not have these needs, and that is okay, but they should choose a different framework in that case. The designers of httpglue do not believe that we can achieve both a framework this small and simple that also caters to every need. Our stance is very strong on this point, and additional features will almost never be added in, except maybe for highly exceptional cases.

### Looking for contributers?

We doubt the core of httpglue (this repo) will ever grow and aquire new features. While we do try to keep an open mind, it is our top priority to keep the featureset and api of this framework as small as is possible, so new feature contributions are generally not a consideration, unless the argument for them is amazingly strong, and even then, there is a strong bias for less rather than more. This all means that ultimately, We're not looking for additional contributers at this time.

However, in our opinion, one of the best ways to contribute is not to work on this core project but to actually create your own projects that are built to work nicely with or extend httpglue. In this fasion, you're contributing to the 'httpglue ecosystem'. If you want to associate them with the project feel free to add the "Framework :: httpglue" classifier. 

These kinds of contributions are of incredible value to the project. httpglue does so little on it's own; As much as this is a strength, it is also a weakness. A strong ecosystem where people can handpick out the specific extensions and tools they need will go a long way towards making httpglue more productive and enjoyable to use.

This is 'horizontally scaled' open source, using more brains to make and manage more projects rather than more brains to grow and manage one project.