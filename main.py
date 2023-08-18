import socket
import ssl
import time
import threading
import signal
import os
import secrets
import sys

#192.168.1.15
conn_list = dict()  #contains the threads
object_list = dict()  #contains the sockets
data_list = list()  #contains the thread id's
group_list = dict()  #list of users toggled group chat
token = 0
token_list = dict()  #users coupled with their tokens
allowed = list("qwertyuopasdfghjklizxcvbnm" + "qwertyuopasdfghjklizxcvbnm".upper() + "1234567890_")
forbidden_usernames = ["quit", "status", "toggle", "admin", "upload", "download", "online", "new_target"]
restricted = ["main.py", "client.py", "user.csv", "UserError.txt", "banned.csv"]  # put the crucial files of the server here
allowance = dict()  #  upload download collisions are prevented with this
ip_list = dict()  #  this is for managing bans only
admin_command_list = ["online", "kick", "ban", "msg", "g", "s"]
message_queue = list()

def kick(user: str):
    """

    :param user: Assigned username obtained by AUTH
    :return: Returns nothing

    Better designing and structuring of code.
    I left the replaced code as comments so that i
    can roll back rapidly in case.
    """
    global object_list, conn_list, token_list, group_list, allowance, user_thread_list
    try:
        object_list[user].close()
    except:
        print(f"<connection did not close for {user} - proceeding to empty from database>")
    object_list.pop(user)
    conn_list.pop(user)
    token_list.pop(user)
    group_list.pop(user)
    ip_list.pop(user)
    allowance.pop(user)
    date = time.asctime()
    date = date.split(" ")
    date = " ".join(date[1:-1])
    print(f"<{user} left> -- {date}")

def hash(a: str):
    """

    :param a: String
    :return: Hash

    A custom code of an md5-like hash. It is important because built-in
    hash's internal state changes every time you start up the program.
    It is crucial for it to remain the same always.
    """
    temp = ""
    for k in a:
        temp += str(bin(ord(k)))
    temp = temp.replace("b", "")
    length = bin(len(a))
    length = str(length.replace("0b", ""))
    length_of_length = len(length)
    padding = 64 - length_of_length
    if len(temp) < 512:
        remainder = 512 - len(temp)
    else:
        remainder = len(temp) % 512
    temp += "1"
    temp += "0" * (remainder - 1)
    temp += "0" * padding
    temp += length

    J = 0x67425301
    K = 0xEDFCBA45
    L = 0x98CBADFE
    M = 0x13DCE476

    def F(K, L, M, J):
        L += M
        result = (K and L) or (not K and M)
        L += result
        L = L << 1
        return L % (pow(2, 32))

    def G(K, L, M, J):
        result = (K and L) or (L and not M)
        M += result
        M = M << 1
        return M % (pow(2, 32))

    def H(K, L, M, J):
        J += M
        result = K ^ L ^ M
        J += result
        J = J << 1
        return J % (pow(2, 32))

    def I(K, L, M, J):
        K += M
        result = L ^ (K or not M)
        K += result
        K = K << 1
        return K % (pow(2, 32))

    l = 0
    for k in range(0, 16):
        message = ""
        for m in range(l, l + 32):
            message += temp[m]
        l += 32
        message = int(message, 2)
        M = (M + message) % pow(2, 32)
        L = F(K, L, M, J)

    l = 0
    for k in range(0, 16):
        message = ""
        for m in range(l, l + 32):
            message += temp[m]
        l += 32
        message = int(message, 2)
        M = (M + message) % pow(2, 32)
        M = G(K, L, M, J)

    l = 0
    for k in range(0, 16):
        message = ""
        for m in range(l, l + 32):
            message += temp[m]
        l += 32
        message = int(message, 2)
        M = (M + message) % pow(2, 32)
        J = H(K, L, M, J)

    l = 0
    for k in range(0, 16):
        message = ""
        for m in range(l, l + 32):
            message += temp[m]
        l += 32
        message = int(message, 2)
        M = (M + message) % pow(2, 32)
        K = I(K, L, M, J)

    end = str(J).replace("0x", "") + str(K).replace("0x", "") + str(L).replace("0x", "") + str(M).replace("0x", "")

    return int(end)

def server_status():
    """

    :return: Returns the server log

    Just logs the servers current state. This is for debugging
    purposes.
    """
    th = "Amount of threads: " + str(len(conn_list))  #Amount of threads
    us = "Amount of users: " + str(len(object_list))
    ls = "List of users: \n" + "\n".join(list(object_list.keys()))
    return th + "\n" + us + "\n" + ls

def intro_handler(connection, address):
    """

    :param connection: SSLSocket object of the accepted connection
    :param address: ip-port tuple
    :return: Returns nothing

    This is the welcome function of the server. Runs one cycle only.
    Then either cedes to handler, put_hanler or kicks the user and
    returns.
    """
    global data_list, object_list, conn_list, token_list, f, allowance
    data_list.append(threading.get_ident())
    mes = connection.read(4096)
    mes = str(mes)[2:-1].split(" ")
    if not (mes[0] == "AUTH" or mes[0] == "PUT"):
        connection.write(bytes("END * <incorrect protocol> \r\n", "utf-8"))
        connection.close()
    elif mes[0] == "PUT" and not (mes[1] in f.keys()):
        c = True
        for a in mes[1]:
            if a not in allowed:
                c = False
        if mes[1].lower() in forbidden_usernames:  #so there is no case distinction
            c = False
        if len(mes[1]) > 15:
            c = False
        if c:
            with open("user.csv", "a") as file:
                file.write(f"{str(mes[1])},{str(hash(mes[2]))}\n")
            f[mes[1]] = str(hash(mes[2]))  # appends the data to the ram
            token = secrets.randbits(16)
            token_list[mes[1]] = token
            allowance[mes[1]] = 0
            connection.write(bytes(f"ACCEPT {mes[1]} {token} \r\n", "utf-8"))
            date = time.asctime()
            date = date.split(" ")
            date = " ".join(date[1:-1])
            print(f"<{mes[1]} joined and accepted> -- {date}")
            conn_list[mes[1]] = threading.Thread(target=handler, args=[conn, addr[0], addr[1], mes[1], token])
            object_list[mes[1]] = connection
            conn_list[mes[1]].start()
        else:
            threading.Thread(target=put_handler, args=[connection, address[0], address[1], c]).start()
    elif mes[0] == "PUT":
        threading.Thread(target=put_handler, args=[connection, address[0], address[1], True]).start()
    #normal log in
    elif mes[1] in f.keys():
        if not f[mes[1]] == str(hash(mes[2])):
            connection.write(bytes("END <incorrect username or password> \r\n", "utf-8"))
            connection.close()
        elif mes[1] in object_list.keys():
            connection.write(bytes("END * <user already online> \r\n", "utf-8"))
            connection.close()
        else:
            token = secrets.randbits(16)
            token_list[mes[1]] = token
            allowance[mes[1]] = 0
            connection.write(bytes(f"ACCEPT {mes[1]} {token} \r\n", "utf-8"))
            date = time.asctime()
            date = date.split(" ")
            date = " ".join(date[1:-1])
            print(f"<{mes[1]} accepted> -- {date}")
            conn_list[mes[1]] = threading.Thread(target=handler,
                                                 args=[connection, address[0], address[1], mes[1], token])
            object_list[mes[1]] = connection
            conn_list[mes[1]].start()
    elif mes[1] in object_list.keys():
        connection.write(bytes("END * <user already online> \r\n", "utf-8"))
        connection.close()
    else:
        connection.write(bytes("END <incorrect username or password> \r\n", "utf-8"))
        connection.close()

def handler(con, ip, port, user, t):
    """
    :param con: Client connection object as SSLSocket
    :param ip: Client ip
    :param port: Client port
    :param user: Assigned username obtained by AUTH
    :param t: Assigned token for the user
    :return: Returns nothing

    Handles everything about the user specified by arguments.
    Does both receiving sending messages. This function is
    called within another thread after user logs in or signs up.
    """
    global conn_list, data_list, object_list, group_list, token_list, allowance, ip_list, message_queue
    data_list.append(threading.get_ident())
    group_list[user] = False
    ip_list[user] = ip
    address = (ip, port)
    received = 0
    try:
        while True:
            me = con.read(4096)  #changed the name of this so i can log it as the last query
            mes = str(me)[2:-1].split(" ")
            received = str(mes[-2])
            if received != str(t):
                break
            if mes[0] == "MSG":
                if not (mes[1] in conn_list.keys()):
                    con.write(bytes("CNT <user not online> \r\n", "utf-8"))
                elif mes[2] not in token_list.keys():
                    break
                elif token_list[mes[2]] != token_list[user]:
                    break
                elif received != str(token_list[mes[2]]):
                    # always check the received username for the token
                    break
                elif allowance[mes[1]] != 0:
                    res = " ".join(mes[3:-2])
                    message_queue.append(["RELAY", mes[1], mes[2], res])
                # All the above are controls, this below is the final state, which is to send the message
                else:
                    res = " ".join(mes[3:-2])
                    object_list[mes[1]].write(bytes(f"RELAY {mes[1]} {mes[2]} {res} \r\n", "utf-8"))

            elif mes[0] == "MSGG":
                if mes[1] not in token_list.keys():
                    break
                elif token_list[user] != token_list[mes[1]]:
                    break
                elif received != str(token_list[user]):
                    break
                res = " ".join(mes[2:-2])

                for k in f.keys():
                    #  group list is not emptied when someone leaves the server, keep that in mind
                    if k != mes[1] and (k in object_list.keys()) and group_list[k]:
                        if allowance[k] != 0:
                            message_queue.append(["RELAYG", mes[1], res, k])  # The last one is the "target"
                            continue
                        object_list[k].write(bytes(f"RELAYG {mes[1]} {res} \r\n", "utf-8"))

            elif mes[0] == "CMD":
                if mes[1] == "<online>":
                    l = list(object_list.keys())
                    res = " ".join(l[:100])  # sends only the first 100 people online
                    con.write(bytes(f"CMD <{res}> \r\n", "utf-8"))
                elif mes[1] == "<get>":
                    if allowance[user] != 0:
                        con.write(bytes("STOP <collision detected - wait for a moment before trying again> \r\n", "utf-8"))
                        continue
                    allowance[user] += 1  # Allowance increased
                    file_list = list()
                    with os.popen(f"ls | grep '{user}+'") as sub:  # we put username in grep, beware of injections
                        file_list = [k.replace("\n", "") for k in sub.readlines()]
                    for k in restricted:
                        try:
                            file_list.remove(k)
                        except:
                            pass
                    con.write(bytes(f"BEGIN {str(len(file_list))} \r\n", "utf-8"))
                    for k in file_list:
                        name = k.split("+")[-1]
                        with open(k, "rb") as to_send:
                            con.write(bytes(f"BEGINF {name} \r\n", "utf-8"))
                            data = to_send.read()
                            con.write(data)
                            con.write(bytes("ENDF ENDF ENDF \r\n", "utf-8"))
                    con.write(bytes("CMD <file send complete> \r\n", "utf-8"))
                    allowance[user] -= 1  #  Allowance decreased
                    for k in file_list:
                        os.remove(k)
                elif mes[1] == "<group>":
                    group_list[user] = not group_list[user]

            elif mes[0] == "END":
                con.write(bytes("END <end accepted> \r\n", "utf-8"))
                kick(user)
                break

            elif mes[0] == "BEGINF":
                if allowance[mes[2]] != 0:
                    con.write(bytes("STOP <collision detected - wait for a moment before trying again> \r\n", "utf-8"))
                    continue
                if received != str(token_list[user]):
                    break
                declared_size = int(mes[3])
                if declared_size > 15000000:  #  max file size is 10mb
                    con.write(bytes("STOP <size too big> \r\n", "utf-8"))
                    continue
                filename = mes[2] + "+" + str(secrets.randbits(64)) + mes[1]
                for k in filename:
                    if k not in allowed and k != "." and k != "+":
                        filename = filename.replace(k, "_")

                con.write(bytes("PROCEED \r\n", "utf-8"))
                #important bug solved here
                decreased = False
                try:
                    with open(f"{filename}", "xb") as new_file:
                        measured_size = 0
                        allowance[mes[2]] += 1  # Allowance increased
                        while True:
                            new_data = con.read(4096)
                            measured_size += 4096
                            #  8 kilobytes of margin is left
                            if measured_size > declared_size + 4096*2:
                                con.write(bytes("END <incorrect size declaration> \r\n", "utf-8"))
                                kick(user)
                                allowance[mes[2]] -= 1
                                os.remove(f"{filename}")
                                return
                            str_data = str(new_data)[2:-1].split(" ")
                            if len(str_data) >= 3:
                                if str_data[-3] == "ENDF" and str_data[-2] == str(t):
                                    if not len(str_data) == 3:
                                        last_data = bytes(" ".join(list(str_data)[:-3]))
                                        new_file.write(last_data)
                                    break

                            new_file.write(new_data)
                    con.write(bytes("CMD <upload complete> \r\n", "utf-8"))
                    time.sleep(2)
                    allowance[mes[2]] -= 1
                    decreased = True
                    continue
                except Exception as e:
                    if not decreased:
                        allowance[mes[2]] -= 1
                        decreased = True
                    print(e)
                    con.write(bytes("CMD <problem with command> \r\n", "utf-8"))

            else:
                try:
                    object_list[mes[1]].send(bytes("END * <incorrect protocol> \r\n", "utf-8"))
                except:
                    pass
                kick(user)
                break
        # out of the loop
        try:
            object_list[mes[1]].send(bytes("END * <incorrect protocol> \r\n", "utf-8"))
            kick(user)
            date = time.asctime()
            with open("UserError.txt", "a") as er:
                er.write("\n----------\n")
                er.write(f"Incorrect protocol at {date} from {user}\n")
                er.write(f"User info: {user} | {ip}:{port} | {t}\n")
                er.write("Last query:\n")
                er.write(f"{str(me)}\n")
        except:
            pass

    except IndexError as e:
        object_list[user].write(bytes("END <an error has occured - consult the admin> \r\n", "utf-8"))
        kick(user)
        date = time.asctime()
        with open("UserError.txt", "a") as er:
            er.write("\n----------\n")
            er.write(f"IndexError: {e} at {date} from {user}\n")
            er.write(f"User info: {user} | {ip}:{port} | {t}\n")
            er.write("No query received\n")
    except ConnectionResetError as e:
        object_list[user].write(bytes("END <an error has occured - consult the admin> \r\n", "utf-8"))
        kick(user)
        date = time.asctime()
        with open("UserError.txt", "a") as er:
            er.write("\n----------\n")
            er.write(f"ConnectionResetError: {e} at {date} from {user}\n")
            er.write(f"User info: {user} | {ip}:{port} | {t}\n")
            er.write("No query received\n")
    except ValueError as e:
        object_list[user].write(bytes("END <an error has occured - consult the admin> \r\n", "utf-8"))
        kick(user)
        date = time.asctime()
        with open("UserError.txt", "a") as er:
            er.write("\n----------\n")
            er.write(f"ValueError: {e} at {date} from {user}\n")
            er.write(f"User info: {user} | {ip}:{port} | {t}\n")
            er.write("No query received\n")
    except OSError as e:
        try:
            object_list[user].write(bytes("END <an error has occured - consult the admin> \r\n", "utf-8"))
        except:
            pass
        date = time.asctime()
        # These files will not be reachable with ftp because they have spaces in them
        # But i added the UserError.txt to the important files list just in case.
        with open(f"FatalUserError at {date}.txt", "x") as er:
            er.write(f"OSError: {e} at {date} from {user}\n")
            er.write(f"User info: {user} | {ip}:{port} | {t}\n")
            er.write("No query received\n")
            er.write("Current server status:\n")
            er.write(server_status())
        try:
            kick(user)
        except:
            pass
    except RuntimeError as e:
        date = time.asctime()
        with open(f"FatalUserError at {date}.txt", "x") as er:
            er.write(f"OSError: {e} at {date} from {user}\n")
            er.write(f"User info: {user} | {ip}:{port} | {t}\n")
            er.write("No query received\n")
            er.write("Current server status:\n")
            er.write(server_status())
        # Let's not handle it for now

def check():
    """

    :return: Returns nothing

    Closes down broken connections that got left open on the
    server side. Some sort of DDoS prevention code.
    """
    global data_list
    data_list.append(threading.get_ident())
    while True:
        time.sleep(15)
        try:
            for k, v in object_list.items():
                try:
                    v.write(bytes("CHECK \r\n", "utf-8"))
                except:
                    try:
                        v.close()
                    except:
                        pass
                    object_list.pop(k)
        except RuntimeError:
            pass

def admin():
    """

    :return: Returns nothing

    Manages the admin power.
    """
    global bans
    while True:
        print("Enter your command: ", end="")
        cmd = sys.stdin.readline(4096)
        cmd = str(cmd).replace("\n", "")
        if cmd[0] == "/":
            cmd = cmd[1:]
            cmd = cmd.split(" ")
            if cmd[0] == "online":
                print("<", end="")
                print(" ".join(list(object_list.keys())), end="")
                print(">")
            elif cmd[0] == "kick":
                user = cmd[1]
                object_list[user].write(bytes("END <you are being kicked> \r\n", "utf-8"))
                kick(user)
            elif cmd[0] == "ban":
                user = cmd[1]
                ip = ip_list[user]
                bans.append(str(ip))
                with open("banned.csv", "a") as file:
                    file.write(str(ip) + "\n")
                object_list[user].write(bytes("END <you are banned> \r\n", "utf-8"))
                kick(user)
            elif cmd[0] == "msg":
                user = cmd[1]
                mes = " ".join(cmd[2:])
                object_list[user].write(bytes(f"RELAY {user} admin {mes}... \r\n", "utf-8"))
            elif cmd[0] == "g":
                mes = " ".join(cmd[1:])
                for k, v in object_list.items():
                    v.write(bytes(f"RELAYG {k} admin {mes}... \r\n", "utf-8"))
            elif cmd[0] == "s":
                print(server_status())

def queue():
    """

    :return: Returns nothing

    This function is called ona seperate thread
    at the servers start up. It manages the message
    queue for the transmission control.
    """
    global message_queue
    while True:
        the_copy = message_queue.copy()
        # I know all the elements are lists too, therefore their id's remain the same
        # But we don't do any change on them, just read from them.
        for k in the_copy:
            if k[0] == "RELAY" and allowance[k[1]] == 0:
                try:
                    object_list[k[1]].write(bytes(f"RELAY {k[1]} {k[2]} {k[3]} \r\n", "utf-8"))
                    index = message_queue.index(k)
                    message_queue.pop(index)
                except:
                    pass
            elif k[0] == "RELAYG" and allowance[k[-1]] == 0:
                try:
                    object_list[k[-1]].write(bytes(f"RELAYG {k[1]} {k[2]} \r\n", "utf-8"))
                    index = message_queue.index(k)
                    message_queue.pop(index)
                except:
                    pass

        time.sleep(0.01)


#  I did not put any logging here because if anything happens, we can just kick the person out.
#  Literally who cares.
def put_handler(con, ip, port, control):
    """

    :param con: SSLSocket object of the accepted connection
    :param ip: ip of the client
    :param port: port of the user
    :param control: Internal server parameter
    :return: Returns nothing

    This function manages the signup process. Every user gets 60
    trials. This is to prevent DDoS. Either cedes to handler or
    kicks the user and returns.
    """
    temp_name = str(secrets.randbits(64))
    global conn_list, data_list, object_list, token_list, f, allowance
    data_list.append(threading.get_ident())
    object_list[temp_name] = con
    try:
        count = 0
        while count < 60:
            if control:
                con.write(bytes("TRY <username already taken> \r\n", "utf-8"))
            else:
                con.write(bytes("TRY <disallowed characters or length> \r\n", "utf-8"))
            mess = con.read(4096)
            mess = str(mess)[2:-1].split(" ")
            if len(mess[1]) > 15:
                control = False
            if mess[1].lower() in forbidden_usernames:
                control = False
            else:  #enter this loop only when needed, small optimization
                for k in mess[1]:
                    if k not in allowed:
                        control = False
                        break
                    else:
                        control = True
            if mess[0] == "PUT" and not (mess[1] in f.keys()) and control:
                with open("user.csv", "a") as x:
                    x.write(f"{str(mess[1])},{str(hash(mess[2]))}\n")
                f[mess[1]] = str(hash(mess[2]))  # appends the data to the ram
                token = secrets.randbits(16)
                token_list[mess[1]] = token
                allowance[mess[1]] = 0
                con.write(bytes(f"ACCEPT {mess[1]} {token} \r\n", "utf-8"))
                date = time.asctime()
                date = date.split(" ")
                date = " ".join(date[1:-1])
                print(f"<{mess[1]} joined and accepted> -- {date}")
                conn_list[mess[1]] = threading.Thread(target=handler, args=[con, ip, port, mess[1], token])
                object_list[mess[1]] = con
                object_list.pop(temp_name)
                conn_list[mess[1]].start()
                break
            count += 1
        if count > 59:
            con.write(bytes("END <too many trials> \r\n", "utf-8"))
            con.close()
    except:
        object_list.pop(temp_name)
        con.close()


try:
    with open("user.csv", "r") as file:
        lines = file.readlines()
        #  Some compilers for some reason put an empty string at the end of this
        lines = list(filter(lambda x: x != "", lines))
        f = {k.split(",")[0]: k.split(",")[1].replace("\n", "") for k in lines}
        #  allowance = {k: 0 for k in f.keys()}
        #  now this is created on users login

    with open("banned.csv", "r") as file:
        bans = file.readlines()
    bans = list(map(lambda x: x.replace("\n", ""), bans))


    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain("../cert.pem", "../cert.pem")
    context.verify_mode &= ~ssl.CERT_REQUIRED

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        #172.31.19.23
        server.bind(("172.31.19.23", 18443))
        server.listen(5)

        with context.wrap_socket(server, server_side=True) as secure_server:
            # Server initialization happens here, after the ssl socket
            # becomes active.

            # threading.Thread(target=check).start()
            """
            Check function will be disabled for now. It causes many problems 
            and interruptions in client-server talk.
            """
            threading.Thread(target=admin).start()
            threading.Thread(target=queue).start()
            while True:
                conn, addr = secure_server.accept()
                if str(addr[0]) in bans:
                    conn.close()
                else:
                    threading.Thread(target=intro_handler, args=[conn, addr]).start()


except ssl.SSLError as e:
    date = time.asctime()
    with open(f"FatalError at {date}.txt", "x") as er:
        er.write(f"An unexpected error occured at {date}:\n")
        er.write(f"{e}\n")
        er.write("----------\n")
        er.write("Current server status:\n")
        er.write(server_status())
    print("<TLS connection error>")
    quit()
except Exception as e:
    print(f"An unexpected error has occured: {e}")
    date = time.asctime()
    with open(f"FatalError at {date}.txt", "x") as er:
        er.write(f"An unexpected error occured at {date}:\n")
        er.write(f"{e}\n")
        er.write("----------\n")
        er.write("Current server status:\n")
        er.write(server_status())
    try:
        for k, v in object_list.items():
            v.write(bytes("END * <internal server error> \r\n", "utf-8"))
            v.close()
        if os.name != "nt":
            for k in data_list:
                signal.pthread_kill(k, signal.SIGKILL)
    except:
        pass
