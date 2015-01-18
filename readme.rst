Pushbullet-RPC
==============
Design principle based on python SimpleXMLRPCServer.

Using Pushbullet `note` for calling python functions. The note `title` used as function name and the `body` contains the function parameter when necessary.


Installation
------------
:: 

    git clone https://github.com/kovacsbalu/pushbullet-rpc
    cd pushbullet-rpc


Requirements
------------

-  pushbullet.py (https://github.com/randomchars/pushbullet.py)

Usage
-----
Check example.py


Tests
-----
::
    $ py.test tests.py
