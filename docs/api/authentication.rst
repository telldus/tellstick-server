
Authentication
==============

Before making any REST calls to TellStick ZNet the application must request a
token that the user has authenticated.

Step 1 - Request a request token
################################

Request a request token by performing a PUT call to the endpoint /api/token. You
need to supply the application name as a parameter "app"

.. code::

   $ curl -i -d app="Example app" -X PUT http://0.0.0.0/api/token
   HTTP/1.1 200 OK
   Date: Fri, 15 Jan 2016 13:33:54 GMT
   Content-Length: 148
   Content-Type: text/html;charset=utf-8
   Server: CherryPy/3.8.0

   {
     "authUrl": "http://0.0.0.0/api/authorize?token=0996b21ee3f74d2b99568d8207a8add9",
     "token": "0996b21ee3f74d2b99568d8207a8add9"
   }

Step 2 - Authenticate the app
#############################

Redirect the user to the url returned in step 1 to let him/her authenticate the
app.

Step 3 - Exchange the request token for an access token
#######################################################

When the user has authenticated the request token in step 2 the application
needs to exchange this for an access token. The access token can be used in the
API requests. To exchange the request token for an access token perform a GET
call to the same endpoint in step 1. Supply the request token as the parameter
"token".

.. code::

   $ curl -i -X GET http://0.0.0.0/api/token?token=0996b21ee3f74d2b99568d8207a8add9
   HTTP/1.1 200 OK
   Date: Fri, 15 Jan 2016 13:39:22 GMT
   Content-Length: 230
   Content-Type: text/html;charset=utf-8
   Server: CherryPy/3.8.0

   {
     "allowRenew": true,
     "expires": 1452951562,
     "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImF1ZCI6IkV4YW1wbGUgYXBwIiwiZXhwIjoxNDUyOTUxNTYyfQ.eyJyZW5ldyI6dHJ1ZSwidHRsIjo4NjQwMH0.HeqoFM6-K5IuQa08Zr9HM9V2TKGRI9VxXlgdsutP7sg"
   }

If the returned data contains allowRenew=true then the token was authorized to
renew its expiration itself without letting the user authorize the app again.
The application must renew the token before it expires or else the application
must start the autorization again from step 1.

If allowRenew is not set to true it is not possible for the app to renew the
token and it will always expire after the time set in the parameter "expires".

Step 4 - Making a request
#########################

To make a requst to a TellStick ZNet API endpoint the token in step 3 must be
supplied as a bearer token in the header. This is an example requesting a list
of devices:

.. code::

   $ curl -i -X GET http://0.0.0.0/api/devices/list?supportedMethods=3 -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImF1ZCI6IkV4YW1wbGUgYXBwIiwiZXhwIjoxNDUyOTUxNTYyfQ.eyJyZW5ldyI6dHJ1ZSwidHRsIjo4NjQwMH0.HeqoFM6-K5IuQa08Zr9HM9V2TKGRI9VxXlgdsutP7sg"
   HTTP/1.1 200 OK
   Date: Tue, 19 Jan 2016 10:21:29 GMT
   Content-Type: Content-Type: application/json; charset=utf-8
   Server: CherryPy/3.7.0

   {
     "device": [
       {
         "id": 1,
         "methods": 3,
         "name": "Example device",
         "state": 2,
         "statevalue": "",
         "type": "device"
       }
     ]
   }

Refreshing a token
##################

If the user allowed the application to renew the token in steg 2 it can be
renewed by the calling application. The token must be refreshed before it
expires. If the token has expired the authentication must be restarted from
step 1 again.

.. code::

   $ curl -i -X GET http://0.0.0.0/api/refreshToken -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImF1ZCI6IkV4YW1wbGUgYXBwIiwiZXhwIjoxNDUyOTUxNTYyfQ.eyJyZW5ldyI6dHJ1ZSwidHRsIjo4NjQwMH0.HeqoFM6-K5IuQa08Zr9HM9V2TKGRI9VxXlgdsutP7sg"
   HTTP/1.1 200 OK
   Date: Tue, 19 Jan 2016 10:21:29 GMT
   Content-Type: Content-Type: application/json; charset=utf-8
   Server: CherryPy/3.7.0

   {
     "expires": 1455295348,
     "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImF1ZCI6IkV4YW1wbGUgYXBwIiwiZXhwIjoxNDU1Mjk1MzQ4fQ.eyJyZW5ldyI6dHJ1ZSwidHRsIjo4NjQwMH0.M4il4_2SqJwlCjmuXlU5DS6h-gX7493Tnk9oBJXbgPw"
   }

The new token returned must be used from now on and the old be discarded.
