
Intro
-----

TellStick ZNet offers two ways of integrating custom scripts. They can be
written in either Python or Lua. The difference is outlined below.

Python
######

Python plugins are only available for TellStick ZNet Pro. Python plugins cannot
be run on TellStick ZNet Lite. Python plugins offers the most flexible solution
since full access to the service is exposed. This also makes it fragile since
Python plugins can affect the service negative.

Lua
###

Lua code is available on both TellStick ZNet Pro and TellStick ZNet Lite. Lua
code runs in a sandbox and has only limited access to the system.

To create a Lua script you need to access the local web server in TellStick ZNet.
Browse to: http://[ipaddress]/lua to access the editor.

Lua codes works by signals from the server triggers the execution.
