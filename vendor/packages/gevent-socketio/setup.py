from setuptools import setup, find_packages

setup(
    name="gevent-socketio",
    version="0.2.1",
    description="SocketIO server based on the Gevent pywsgi server, a Python network library",
    #long_description=open("README.rst").read(),
    author="Jeffrey Gelens",
    author_email="jeffrey@noppo.pro",
    license="BSD",
    url="http://www.gelens.org/code/socketio/",
    download_url="http://www.gelens.org/code/socketio/",
    install_requires=("gevent-websocket"),
    packages=find_packages(exclude=["examples","tests"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
    ],
)
