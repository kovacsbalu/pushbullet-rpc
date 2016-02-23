Pushbullet-RPC
==============
Design principle based on python SimpleXMLRPCServer.

Use Pushbullet *note* for calling python functions. The note *title* used as function name and the *body* contains the function parameter when necessary.

.. image:: https://travis-ci.org/kovacsbalu/pushbullet-rpc.svg?branch=master
    :target: https://travis-ci.org/kovacsbalu/pushbullet-rpc 

.. image:: https://coveralls.io/repos/github/kovacsbalu/pushbullet-rpc/badge.svg?branch=master
    :target: https://coveralls.io/github/kovacsbalu/pushbullet-rpc?branch=master

Installation
------------
:: 

    git clone https://github.com/kovacsbalu/pushbullet-rpc
    cd pushbullet-rpc


Requirements
------------

-  python **2.7.x**
-  python built in json
-  pushbullet.py **v0.8.1** (https://github.com/randomchars/pushbullet.py)
-  websocket **v0.23.0** (https://github.com/liris/websocket-client)

Usage
-----
Check ``example.py``


Tests
-----
::

    py.test tests.py
    
with coverage:
::

    py.test --cov-report term-missing --cov pushbulletrpc tests.py
    
