from setuptools import setup

setup(
    name='httpglue',
    version='1.0.0',
    author='Joseph P McAnulty',
    author_email='joedeveloper55@gmail.com',
    py_modules=['httpglue'],
    url='https://github.com/joedeveloper55/httpglue',
    download_url='',
    description='an extremely minimal python http application framework for rest api microservices, supports wsgi or asgi',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Framework :: httpglue",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Internet :: WWW/HTTP :: ASGI",
        "Topic :: Internet :: WWW/HTTP :: ASGI :: Application",
        "Topic :: Software Development :: Libraries :: Application Frameworks"
    ],
    python_requires='>=3.6'
)