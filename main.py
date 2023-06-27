import socket
import ssl
import time
import threading
import signal
import os
import secrets

conn_list = dict()  #contains the threads
object_list = dict()  #contains the sockets
data_list = list()  #contains the thread id's
token = 0
allowed = list("qwertyuopasdfghjklizxcvbnm" + "qwertyuopasdfghjklizxcvbnm".upper() + "1234567890_")
restricted = ["main.py", "client.py", "user.csv"]  # put the crucial files of the server here
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

def handler(con, ip, port, user, t):
    global conn_list, data_list, object_list
    data_list.append(threading.get_ident())
    address = (ip, port)
    received = 0
    try:
        while True:
            mes = con.read(4096)
            mes = str(mes)[2:-1].split(" ")
            received = str(mes[-2])
            if received != str(t):
                break
            if mes[0] == "MSG":
                if not (mes[1] in conn_list.keys()):
                    con.write(bytes("CNT <user not online> \r\n", "utf-8"))
                else:
                    res = " ".join(mes[3:-2])
                    object_list[mes[1]].write(bytes(f"RELAY {mes[1]} {mes[2]} {res} \r\n", "utf-8"))
            elif mes[0] == "MSGG":
                res = " ".join(mes[2:-2])
                for k in f.keys():
                    if k != mes[1] and k in object_list.keys():
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
                            time.sleep(1)
                            data = to_send.read()
                            con.write(data)
                            time.sleep(5)
                            con.write(bytes("ENDF \r\n", "utf-8"))
                    con.write(bytes("CMD <file send complete> \r\n", "utf-8"))
                    for k in file_list:
                        os.remove(k)


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
                filename = mes[2] + "+" + mes[1]
                try:
                    with open(filename, "xb") as new_file:
                        begin = time.time()
                        while True:
                            new_data = con.read(4096 * 4096)
                            str_data = str(new_data)[2:-1].split(" ")
                            end = time.time()
                            if str_data[0] == "ENDF" and str_data[1] == str(t) and str_data[2] == "\r\n":
                                break
                            elif end - begin > 5:
                                break
                            new_file.write(new_data)
                    con.write(bytes("CMD <upload complete> \r\n", "utf-8"))
                    continue
                except:
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
            conn_list.pop(user)
            date = time.asctime()
            date = date.split(" ")
            date = " ".join(date[1:-1])
            print(f"<{user} left> -- {date}")
        except:
            pass

    except IndexError:
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
    except ConnectionResetError:
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
    except ValueError:
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
    except OSError:
        for k, v in object_list.items():
            try:
                v.close()
            except:
                pass
        print("<server closing>")
        exit()
    except RuntimeError:
        pass

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


def put_handler(con, ip, port, control):
    temp_name = str(secrets.randbits(64))
    global conn_list, data_list, object_list
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
                file.write(f"{str(mess[1])},{str(hash(mess[2]))}\n")
                f[mess[1]] = str(hash(mess[2]))  # appends the data to the ram
                token = secrets.randbits(16)
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

    with open("user.csv", "a") as file:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain("../cert.pem", "../cert.pem")
        context.verify_mode &= ~ssl.CERT_REQUIRED

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(("192.168.1.38", 18443))
            server.listen(5)

            with context.wrap_socket(server, server_side=True) as secure_server:
                threading.Thread(target=check).start()
                while True:
                    conn, addr = secure_server.accept()

                    mes = conn.read(4096)
                    mes = str(mes)[2:-1].split(" ")
                    if not (mes[0] == "AUTH" or mes[0] == "PUT"):
                        conn.write(bytes("END * <incorrect protocol> \r\n", "utf-8"))
                        conn.close()
                    # signing up
                    elif mes[0] == "PUT" and not (mes[1] in f.keys()):
                        c = True
                        for a in mes[1]:
                            if a not in allowed:
                                c = False
                        if c:
                            file.write(f"{str(mes[1])},{str(hash(mes[2]))}\n")
                            f[mes[1]] = str(hash(mes[2]))  # appends the data to the ram
                            token = secrets.randbits(16)
                            conn.write(bytes(f"ACCEPT {mes[1]} {token} \r\n", "utf-8"))
                            date = time.asctime()
                            date = date.split(" ")
                            date = " ".join(date[1:-1])
                            print(f"<{mes[1]} joined and accepted> -- {date}")
                            conn_list[mes[1]] = threading.Thread(target=handler, args=[conn, addr[0], addr[1], mes[1], token])
                            object_list[mes[1]] = conn
                            conn_list[mes[1]].start()
                        else:
                            threading.Thread(target=put_handler, args=[conn, addr[0], addr[1], c]).start()
                    elif mes[0] == "PUT":  # mess instead of mes
                        threading.Thread(target=put_handler, args=[conn, addr[0], addr[1], True]).start()
                    # normal log in
                    elif not f[mes[1]] == str(hash(mes[2])):
                        print(f[mes[1]])
                        print(hash(mes[2]))
                        conn.write(bytes("END <incorrect username or password> \r\n", "utf-8"))
                        conn.close()
                    elif mes[1] in object_list.keys():
                        conn.write(bytes("END * <user already online> \r\n", "utf-8"))
                        conn.close()
                    else:
                        token = secrets.randbits(16)
                        conn.write(bytes(f"ACCEPT {mes[1]} {token} \r\n", "utf-8"))
                        date = time.asctime()
                        date = date.split(" ")
                        date = " ".join(date[1:-1])
                        print(f"<{mes[1]} accepted> -- {date}")
                        conn_list[mes[1]] = threading.Thread(target=handler, args=[conn, addr[0], addr[1], mes[1], token])
                        object_list[mes[1]] = conn
                        conn_list[mes[1]].start()
except:
    try:
        for k, v in object_list.items():
            v.write(bytes("END * <internal server error> \r\n", "utf-8"))
            v.close()
        if os.name != "nt":
            for k in data_list:
                signal.pthread_kill(k, signal.SIGKILL)
    except:
        pass




