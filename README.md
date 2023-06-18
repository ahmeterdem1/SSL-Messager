# SSL-Messager 

A basic cyphered tool for messaging.

## System

main.py file is the server, and client.py file is obviously the client.
user.csv file is to check for username and password. After users log in,
they choose a target to send messages to. If the user is online, messages
are sent. If not, a harmless error message is printed.

There is no peer to peer connection. Everybody is connected to the server,
and sends messages to the server. Server then relays these messages to
intended targets. One can only send message to one person at this version,
but can receive from multiple users.

Self-signed certificates are required.

A thread is created for each user in the server. This thread handles both
receiving from this user, and sending messages to targets. Also another thread
is created in the server to check if the connections are still alive. If not,
closes server-sided sockets and as a resulting exception, related threads return.

In the client side 2 threads exist. One is for receiving and printing out messages,
the other is for getting input from the user and sending messages.

## Protocol

Without any user online, server just sits silently. When a user is trying to log in,
following sentence is sent:

`AUTH username password \r\n`

In response, if accepted, server answers with the following reply:

`ACCEPT username \r\n`

If not accepted:

`END <incorrect username or password> \r\n`

To send messages, client sends the following query:

`MSG target username message \r\n`

Server redirects this message to the target in the exact same order, except the first word:

`RELAY target username message \r\n`

To check if a client socket is online, server tries to send the following message (no response needed):

`CHECK \r\n`

If any sent query does not in the form stated above, server sends the following query and closes down
the socket unilaterally:

`END * <incorrect protocol>`

### Important notes on the protocol

- MSG and AUTH flagged messages can only be sent from the client.
- All other messages are sent by the server.
- Every query ends with "\r\n" but this does not serve a purpose for now.
- Server messages about errors are written inside <> sings