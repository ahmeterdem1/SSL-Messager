import socket
import ssl
import time
import threading
import signal
import os
import secrets

#192.168.1.15
conn_list = dict()  #contains the threads
object_list = dict()  #contains the sockets
data_list = list()  #contains the thread id's
group_list = dict()  #list of users toggled group chat
token = 0
token_list = dict()  #users coupled with their tokens
allowed = list("qwertyuopasdfghjklizxcvbnm" + "qwertyuopasdfghjklizxcvbnm".upper() + "1234567890_")
restricted = ["main.py", "client.py", "user.csv", "UserError.txt"]  # put the crucial files of the server here
def hash(a: str):
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
    th = "Amount of threads: " + str(len(conn_list))  #Amount of threads
    us = "Amount of users: " + str(len(object_list))
    ls = "List of users: \n" + "\n".join(list(object_list.keys()))
    return th + "\n" + us + "\n" + ls

def intro_handler(connection, address):
    global data_list, object_list, conn_list, token_list
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
        if c:
            with open("user.csv", "a") as file:
                file.write(f"{str(mes[1])},{str(hash(mes[2]))}\n")
            f[mes[1]] = str(hash(mes[2]))  # appends the data to the ram
            token = secrets.randbits(16)
            token_list[mes[1]] = token
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
    elif mes[0] == "PUT":  # mess instead of mes
        threading.Thread(target=put_handler, args=[connection, address[0], address[1], True]).start()
    #normal log in
    elif mes[1] in f.keys():
        if not f[mes[1]] == str(hash(mes[2])):
            print(f[mes[1]])
            print(hash(mes[2]))
            connection.write(bytes("END <incorrect username or password> \r\n", "utf-8"))
            connection.close()
        elif mes[1] in object_list.keys():
            connection.write(bytes("END * <user already online> \r\n", "utf-8"))
            connection.close()
        else:
            token = secrets.randbits(16)
            token_list[mes[1]] = token
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
        token = secrets.randbits(16)
        token_list[mes[1]] = token
        connection.write(bytes(f"ACCEPT {mes[1]} {token} \r\n", "utf-8"))
        print("bruh")
        date = time.asctime()
        date = date.split(" ")
        date = " ".join(date[1:-1])
        print(f"<{mes[1]} accepted> -- {date}")
        conn_list[mes[1]] = threading.Thread(target=handler, args=[connection, address[0], address[1], mes[1], token])
        object_list[mes[1]] = connection
        conn_list[mes[1]].start()


def handler(con, ip, port, user, t):
    global conn_list, data_list, object_list, group_list, token_list
    data_list.append(threading.get_ident())
    group_list[user] = False
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
                    print(mes[2])
                    print(received)
                    print(token_list[user])
                    # always check the received username for the token
                    break
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
                    if k != mes[1] and (k in object_list.keys()) and group_list[k]:
                        object_list[k].write(bytes(f"RELAYG {mes[1]} {res} \r\n", "utf-8"))

            elif mes[0] == "CMD":
                if mes[1] == "<online>":
                    l = list(object_list.keys())
                    res = " ".join(l[:100])  # sends only the first 100 people online
                    con.write(bytes(f"CMD <{res}> \r\n", "utf-8"))
                elif mes[1] == "<get>":
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
                    for k in file_list:
                        os.remove(k)
                elif mes[1] == "<group>":
                    group_list[user] = not group_list[user]

            elif mes[0] == "END":
                con.write(bytes("END <end accepted> \r\n", "utf-8"))
                try:
                    object_list[user].close()
                except:
                    pass
                object_list.pop(user)
                conn_list.pop(user)
                date = time.asctime()
                date = date.split(" ")
                date = " ".join(date[1:-1])
                print(f"<{user} left> -- {date}")
                break

            elif mes[0] == "BEGINF":
                if received != str(token_list[user]):
                    break
                filename = mes[2] + "+" + str(secrets.randbits(64)) + mes[1]
                #important bug solved here
                try:
                    with open(filename, "xb") as new_file:
                        begin = time.time()
                        while True:
                            new_data = con.read(4096)
                            str_data = str(new_data)[2:-1].split(" ")
                            end = time.time()
                            if len(str_data) >= 3:
                                if str_data[-3] == "ENDF" and str_data[-2] == str(t):
                                    if not len(str_data) == 3:
                                        last_data = bytes(" ".join(list(str_data)[:-3]))
                                        new_file.write(last_data)
                                    break

                            if end - begin > 5:
                                break
                            new_file.write(new_data)
                    con.write(bytes("CMD <upload complete> \r\n", "utf-8"))
                    continue
                except Exception as e:
                    print(e)
                    con.write(bytes("CMD <problem with command> \r\n", "utf-8"))

            else:
                try:
                    object_list[mes[1]].send(bytes("END * <incorrect protocol> \r\n", "utf-8"))
                    object_list[user].close()
                except:
                    pass
                object_list.pop(user)
                conn_list.pop(user)
                date = time.asctime()
                date = date.split(" ")
                date = " ".join(date[1:-1])
                print(f"<{user} left> -- {date}")
                break
        # out of the loop
        try:
            object_list[mes[1]].send(bytes("END * <incorrect protocol> \r\n", "utf-8"))
            object_list[user].close()
            object_list.pop(user)
            token_list.pop(user)
            conn_list.pop(user)
            date = time.asctime()
            with open("UserError.txt", "a") as er:
                er.write("\n----------\n")
                er.write(f"Incorrect protocol at {date} from {user}\n")
                er.write(f"User info: {user} | {ip}:{port} | {t}\n")
                er.write("Last query:\n")
                er.write(f"{str(me)}\n")
            date = date.split(" ")
            date = " ".join(date[1:-1])
            print(f"<{user} left> -- {date}")
        except:
            pass

    except IndexError as e:
        try:
            object_list[user].close()
        except:
            pass
        object_list.pop(user)
        conn_list.pop(user)
        token_list.pop(user)
        date = time.asctime()
        with open("UserError.txt", "a") as er:
            er.write("\n----------\n")
            er.write(f"IndexError: {e} at {date} from {user}\n")
            er.write(f"User info: {user} | {ip}:{port} | {t}\n")
            er.write("No query received\n")
        date = date.split(" ")
        date = " ".join(date[1:-1])
        print(f"<{user} left> -- {date}")
    except ConnectionResetError as e:
        try:
            object_list[user].close()
        except:
            pass
        object_list.pop(user)
        conn_list.pop(user)
        token_list.pop(user)
        date = time.asctime()
        with open("UserError.txt", "a") as er:
            er.write("\n----------\n")
            er.write(f"ConnectionResetError: {e} at {date} from {user}\n")
            er.write(f"User info: {user} | {ip}:{port} | {t}\n")
            er.write("No query received\n")
        date = date.split(" ")
        date = " ".join(date[1:-1])
        print(f"<{user} left> -- {date}")
    except ValueError as e:
        try:
            object_list[user].close()
        except:
            pass
        object_list.pop(user)
        conn_list.pop(user)
        token_list.pop(user)
        date = time.asctime()
        with open("UserError.txt", "a") as er:
            er.write("\n----------\n")
            er.write(f"ValueError: {e} at {date} from {user}\n")
            er.write(f"User info: {user} | {ip}:{port} | {t}\n")
            er.write("No query received\n")
        date = date.split(" ")
        date = " ".join(date[1:-1])
        print(f"<{user} left> -- {date}")
    except OSError as e:
        date = time.asctime()
        # These files will not be reachable with ftp because they have spaces in them
        # But i added the UserError.txt to the important files list just in case.
        with open(f"FatalUserError at {date}.txt", "x") as er:
            er.write(f"OSError: {e} at {date} from {user}\n")
            er.write(f"User info: {user} | {ip}:{port} | {t}\n")
            er.write("No query received\n")
            er.write("Current server status:\n")
            er.write(server_status())
        for k, v in object_list.items():
            try:
                v.close()
            except:
                pass
        print("<server closing>")
        exit()
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

#  I did not put any logging here because if anything happens, we can just kick the person out.
#  Literally who cares.
def put_handler(con, ip, port, control):
    temp_name = str(secrets.randbits(64))
    global conn_list, data_list, object_list, token_list, f
    data_list.append(threading.get_ident())
    object_list[temp_name] = con
    try:
        count = 0
        while count < 60:
            if control:
                con.write(bytes("TRY <username already taken> \r\n", "utf-8"))
            else:
                con.write(bytes("TRY <disallowed characters> \r\n", "utf-8"))
            mess = con.read(4096)
            mess = str(mess)[2:-1].split(" ")
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
        f = {k.split(",")[0]: k.split(",")[1].replace("\n", "") for k in lines}

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain("../cert.pem", "../cert.pem")
    context.verify_mode &= ~ssl.CERT_REQUIRED

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        #172.31.19.23
        server.bind(("172.31.19.23", 18443))
        server.listen(5)

        with context.wrap_socket(server, server_side=True) as secure_server:
            threading.Thread(target=check).start()
            while True:
                conn, addr = secure_server.accept()
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
