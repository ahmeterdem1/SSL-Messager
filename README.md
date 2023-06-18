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