# SSL-Messager 

A basic cyphered tool for messaging.

Our service is online now! You may join us by setting up your client system.

## Setup

Put the client.py file in a folder. Put a certc.pem file that you have created 
in the parent folder. You are good to go!

The reason that these both files are not in the same directory is that; if they 
were, my private keys would be in my git folder. I don't want that. So i put them 
in the parent folder. You may change this setup as you wish in the code.

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

banned.csv is an ip list which has all banned ip's. To unban, edit the file.

dev_client.py is to send queries by hand, and therefore to debug. It is a good
tool to see if any malformed queries or injecitons generate.

## Protocol

Without any user online, server just sits silently. When a user is trying to log in,
following sentence is sent:

`AUTH username password \r\n`

In response, if accepted, server answers with the following reply (client receives its token):

`ACCEPT username token \r\n`

If not accepted:

`END <incorrect username or password> \r\n`

To log in, proper syntax is below:

`PUT username password \r\n`

If username already taken, servers response:

`TRY <username already taken> \r\n`

If not, server just sends the _ACCEPT_ query and logs in the user.

To send messages, client sends the following query with its session token:

`MSG target username message token \r\n`

When group chat is enabled:

`MSGG username message token \r\n`

Server redirects this message to the target(s) in the exact same order, except the first word:

`RELAY target username message \r\n`

When group chat is enabled by the sender:

`RELAYG username message \r\n`

To check if a client socket is online, server tries to send the following message (no response needed):

`CHECK \r\n`

If any sent query is not in the form stated above, server sends the following query and closes down
the socket unilaterally:

`END * <incorrect protocol> \r\n`

IF user inputs the command ":quit:", client sends the END command:

`END <user command> token \r\n`

Server replies with:

`END <end accepted> \r\n`

## File Transfer Protocol

Transmission of any file is surrounded by queries. For client and server,
these queries may differ but indeed the system is the same.

Regulation exists when sending data to the server but not vice versa.

Before each FTP action, server checks the queue. If at the same time a file
is being uploaded to that user, it does not permit downloads to that user.
Same goes for vice versa. If someone tries to upload to somebody and that
user is downloading at the same time, upload is not permitted. These are
declared with stop queries.

When client starts file transmission:

`BEGINF filename.extension target size token \r\n`

Since files are uploaded for another user, target is needed.
Server gets the filename and extension from this query. Server
saves the file as _target+filename.extension_.

Server checks the size of the file and permits the user if it is
below the threshold. If below:

`PROCEED \r\n`

If not:

`STOP <size too big> \r\n`

If allowed clients starts sending the data. Server receives this data
by 4kb packets and measures the size during. If the measured size is
bigger than the declared size + 8kb, then server just kicks the user.
The reason for this kick is that, the only way that this could occur
is that, client has changed their code and therefore lied on transmission.
Lying to the server is the ultimate sin here.

Client sends the following query after its transmission ends:

`ENDF token \r\n`

After server receives and saves all the data, responds to indicate completion:

`CMD <upload complete> \r\n`

or

`CMD <problem with command> \r\n`

depending on the success.

When user requests to download files sent to them, a command is sent:

`CMD <get> token \r\n`

Server replies this with a beginning query, this time without the "F" to indicate
there may be multiple files to send:

`BEGIN amount_of_files \r\n`

Here is the important thing, there is no transmission control in servers ftp.
The reason that there is regulation in sending data to the server is that,
server should decide if it trusts the client. But server already trusts the
server. So, client should trust the server too.

Client gets the information on amount of files to receive from this query. After that,
server applies the same method as client, except:

`ENDF ENDF ENDF \r\n`

This tripple "ENDF" is to prevent bugs arising from within the file data. It is not so
probable that the sent data chuck not intended to be the last has the same format as this.
"\r\n" part is not checked, but is assumed to be there while indexing.

File names are sent in raw form, without the "target+" part.

5 second limit is disabled. A TCP-like regulation is added instead.

Keep in mind that, upload is a blocking code for input. In the future, FTP will be carried
to a different socket than the message protocol.


### Important notes on the protocol

- Every query ends with "\r\n" but this does not serve a purpose for now.
- Server messages about errors are written inside <> sings
- Server sends the token once whilst authorizing
- Client sends its token at each query for validation
- At users download request, files intended for them are searched with ls and grep. Beware of injections with username.


## Commands

### :quit:

Closes down the connection by sending END query then quits the program

### :online:

Shows top 100 online users. This limit is for practical reasons.

### :new_target:

Allows user to change targets. Client thread does not get killed. Just
the target changes.

### :toggle:

Toggles the group chat. At log in, group chat is not enabled. Group chat
messages are sent to only those who enabled group chat. Therefore, group
and private chats are separated. Also, terminal turns green if group chat
is enabled.

### :upload:

Upload a file, one at a time.

### :download:

Download all files sent to you. Clears the history, so if commanded again,
no duplicate files are downloaded.

### :help:

Prints other commands descriptions.

### :mute: user1 user2 user3 ...

Mutes the specified users. There may be as many as you wish. Only does
internal actions.

### :unmute: user1 user2 user3 ...

Unmutes the specified users. Same as above otherwise.

### :status:

Shows the current status; target and if group chat is enabled.

## Admin

Admin in this system is not an account. It is just a thread in the server side.
This thread takes input from the user, then acts accordingly. There are 6 commands
in order to moderate and debug.

### /online

Same as :online: in the client side.

### /kick _target_

Kicks the intended user.

### /ban _target_

Ip bans the intended user and kicks them. Banned ip's are stored in the banned.csv
file. This file is read everytime server is started.

### /msg _target_ _message_

Sends message to the target with "admin" as the name. This name is forbidden as a
client account name.

### /g _message_

Sends the message to the group chat.

### /s

Prints the current server status. This is for debug purposes.

## Error Logging

Now server logs some errors. User caused errors that are non-fatal in nature
are collected in a single file called UserError.txt. Fatal user errors all have
their separate files. Same for the internal server errors. Ip logging is done
for user errors. Also if possible their last query is logged too. This is for
debugging purposes. Date and exception types are collected. Usernames and tokens
are collected. Current server status is collected for fatal user or internal errors.
This consists of amount of online users, their usernames and amount of threads.
Future debugging code will come, and this is the beginning of it.

Error log files are not posted here. They are created by the server if needed.

## Debugging

A developper tool has been added now. Method of operation of this is to enter each
query by hand. If any connection loss happens, client reconnects. This takes some
time in the code though. Purpose of this client is to analyze the servers response
in custom inputted circumstances. So far no abnormal response has been observed.

FTP is not supported in this client. Technically yes it can be done. But there is
no proper loop to collect all the file data nor save it.

Response and write times are logged poorly. It is just for in case.

## Notes

### Major security issue solved (22 June 2023)

When trying to sign up, if already taken username inputted, server used to put
the user in *object_list* temporarily by their ip. If another user, logged in,
typed :online: whilst this process, they could see this ip. 

Ip is now switched with a 64-bit random number given as a temporary name.

### Major security issue solved (4 August 2023)

There was a token system in the server side to prevent impersonation. Even
though it was coded in the system, it was completely ineffective. Code for
token checks are improved with the creation of a new data block "token_list".
It is written into when someone logs in to the server. Initial usernames are
coupled with server generated tokens. These tokens are checked every time a
MSG, MSGG or FTP query is received. Therefore all impersonations are prevented
properly now.

### Major security issue solved (11 August 2023)

This one also requires interfering with the client code. If you delete the splits
and other operations on filenames and send your file like that, symbols like \, / 
may be in your file name. This will probably cause a fatal error in the server.
Or maybe even unintentional folder creations. Now filename is accepted in the
formatted string form to prevent injection like errors. Also other characters are
checked and replaced.

### Known problems

#### Log in / Sign up (partially solved)

When someone tries to log in or sign up, their data in the server is carried to
a thread. This thread is not tracked, so there is no timeout for this process.
When someone just sits in the log in/sign up screen, this creates a pending thread
in the server. Build up of these will result in a denial-of-service.

This used not to be in another thread, it was in the main thread. So sitting on the
log screen used to just block the whole server but it is solved since than.

#### Database saving (solved)

The csv file is not closed down until the server naturally closes down. So when it
quits unexpectedly, all newly saved people until then are lost. I did not solve this
issue because i didn't want the speed impact of reopening and reclosing the database
everytime someone signs up. Ideal solution to this is async read-write streams within
the log in screen thread in the server.

#### Unexpected closing down of the server (mostly solved)

Up until this commit, server used to commit suicide after facing the slightest disturbance.
This was indeed intentional. My first goal was to use my own computer as the server, open
to the public. As many of us can guess, this is not a good idea. So i wanted extra security
in my code with minimal effort. So i made the server super sensitive. It used to shutdown
when someone tried to log in with an invalid username. It used to shutdown after receiving
incorrect protocol syntax. And still aggresive behaviour like this can be found in the code.
But the server is getting more and more "normal" over time. And i have changed my mind, now
i use amazons servers instead of my own computer. So more flexible behaviour will continue
to be implemented. I guess my end goal here would be to connect ciphertools and this project
and to create a fully functional and fully custom tls server. So one day i will turn to using
my own computer despite all the possible dangers.

In the recent debugging tests, a server shutdown has never been observed. However there was just
one instance that server kicked everybody but stayed online. The causing error has been identified.

#### Input-Output Mix up

Input and output streams are fed through the same channel, the same terminal. So when more than
one people are texting at the same time, output of a received message will interrupt the
input take. A gui solution is required for that. In action, this becomes kind of annoying
but not that much of a problem.

Indeed if you just ignore the interruption and continue to write then press enter, your whole
message gets sent properly. So, not that much of a problem again.

#### FTP (solved, bug fixed)

FTP is a problem itself. I have coded it very poorly because i got lazy. It is basically
a data collector with a timer in the receiving end, and a normal data streamer in the
sender end. No problem in the sender but receiving is sometimes problematic. Sometimes
some parts of the data are missed and broken files get generated. Since the underlying
protocol here is TCP, this data loss happens internally at the receiver end. Therefore
better code is needed. I have my plans, but there are still some other things to fix 
before that.

A bug is discovered during the improvement of the FTP. If you upload a file and the target
did not download it yet, if you try to upload it again, server raises an OSError and shuts
down because there exists a file with the same name. Now a 64-bit random number string is
added to the name.

#### Database itself (solved)

Database sometimes breakes down for some reason. Empty lines may generate in the csv file.
Users get saved in the database without problems but an error in the client side may
result in a malformed query and this query results in a broken database in the server-side.
Whole file system of this structure will get an update.

A filter function is added to solve this.

#### Character set

Utf-8 is not enough.

#### Prompts

For some reason, prompts don't get displayed properly. This is not about "Enter your message:"
showing up more than 1 line above your cursor, it is what should happen. Sometimes this
prompt never get displayed. And after 10-20 messages all prompts for them get displayed
at the same time in a chain. The solution for this is a gui. Prompt should be a permanent
label on the screen. Message box should be the only dynamic place.

#### Commands (solved)

~~Commands get broken sometimes. This is not about the error message. They just break down
and never produce a result. Unknown reason, may be due to some malformed query.~~

The reason for this problem is the same as below "Users" section. It is now solved.

#### Users (solved)

~~Whole users get broken sometimes. Their messages start to not show up, their commands break
down, etc. This was observed after a disturbance in the database. After a user breaks down,
other users sending messages to that user get affected too because of the RELAY query. This
results in an error message in the servers terminal, but surprisingly server continues to
operate. KeyError is observed on object_list after a user breaks down. This may happen when
a user gets cleared from the lists but their connection objects remain intact. In that case,
the broken users client sees the connection as intact and continues to function. Indeed it is.
But the "pointer" of the connection socket in the server side is lost. Therefore it is unreachable.
Client thinks they are online but they are not reachable from the server or by anybody.
Improving aggressive server action that takes users down the lists when disturbed may be the
solution.~~

The cause has been identified. If you try to log in even if you have never signed up, server
accepts you. You dont get added to the database though. And you are not reachable for this 
exact reason. Your messages get displayed. Thankfully this issue is solved now.


#### Admin (solved)

There is no admin account nor power. This is intentional. This option will be reconsidered
after a gui version is created.

#### 5-second limit (solved, limit disabled)

This certainly breaks down the users. When trying to upload files larger than the obscure limit
defined by the 5-second limit, "A problem has occured" message is obtained right before client
side only disconnection. No disconnect occurs in the server for some reason. User appers as 
online even though kicked in reality. No error message or log is generated in the server. Indeed
logically, there shouldn't be any errors in the server. Server just abruptly saves the file after
5 seconds then continues to listen normally. I have no idea why this happens. I think we need to
get rid of the 5 second rule or we need to add a shutdown protocol just like normal ftp.

#### Logging security (Major)

If the user encounters an error that is loggable in the perfect spot, like the AUTH or PUT query
that would include their password, password gets logged in plain text. That is a major security
issue. but it is easy to solve.

Still, UserError.txt is in the protected file list. No injection is believed to be able to download
that file. Yet.

#### Usernames (solved)

Users having names like commands; quit, toggle, etc. may result in problems. ":" character is not
in the allowed list though.

The reason is the same as above in the "Users" section. It is solved now.

#### Command timing (solved)

This only occures for upload-download commands, and results in an OSError. When somebody uploads
a file to someone else, and this person starts downloading at the same time, the created and still
being filled file gets deleted. This raises an OSError. Everybody gets kicked but the server 
continues to function. Probable solution to this is to queue these two commands for target pairs.
But still, it is very improbable that this will occur. Increased amount of people in the server
does not increase the probability of this happening. This only happens when the receiver and the
sender initiates the given commands at the same time. There are always 1 receiver and 1 sender.

#### Uploads

Some file types don't get sent properly. These include .mp4 and .exe files. There may be more.
Disabling these extensions is the short answer. I have no idea about the proper answer yet.

Probably will disable some other extensions for security reasons, e.g. .bat, .sh, .s, .o, ...

Also for some reason "Bad file descriptor" error is obtained somewhat frequently in large file
uploads-downloads. The reason is yet unknown. But the servers aggresive response to exceptions
has been modeerated to prevent further errors resulting from other errors.