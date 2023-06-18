import socket
import ssl
import time
import threading
import os

conn_list = dict()  #contains the threads
object_list = dict()  #contains the sockets
data_list = list()

def hash(a: str):  #Some 'interpretation' of md5 hash function that I have created.
    temp = ""      #Hash will be used to order user data, then apply binary search to find the relevant data
    for k in a:    #So it is not completely useless. I just wanted to turn this task into a more useful exercise for me.
        temp += str(bin(ord(k)))
    temp = temp.replace("b", "")  #gets 8 bit ascii numbers in a string, has the reduced net length of the message
    length = bin(len(a))  #LENGTH IN BINARY
    length = str(length.replace("0b", ""))  #deletes the first '0b' from the string
    length_of_length = len(length)
    padding = 64 - length_of_length
    if len(temp) < 512:
        remainder = 512 - len(temp)
    else:
        remainder = len(temp) % 512
    temp += "1"
    temp += "0" * (remainder - 1)  # temp is prepared without the length part
    temp += "0" * padding
    temp += length  # now it is fully prepared with all the padding

    J = 0x67425301  #copied these values from geeksforgeeks
    K = 0xEDFCBA45
    L = 0x98CBADFE
    M = 0x13DCE476

    def F(K, L, M, J):
        L += M
        result = (K and L) or (not K and M)  #These definitions of the variable result are from geeksforgeeks too.
        L += result                         #All the other parts are just my interpretation of the explanation of the algorithm.
        L = L << 1          #Apparently what makes hashes 'random' looking is bit-shifting. I discovered that by creating lots of
        return L % (pow(2, 32))  #not working version of md5. When I added the bit shifting that I had been omitting, everything became much more clearer.

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
        for m in range(l, l + 32):  # prepares the message
            message += temp[m]
        l += 32
        message = int(message, 2)
        M = (M + message) % pow(2, 32)
        L = F(K, L, M, J)

    l = 0
    for k in range(0, 16):
        message = ""
        for m in range(l, l + 32):  # prepares the message
            message += temp[m]
        l += 32
        message = int(message, 2)
        M = (M + message) % pow(2, 32)
        M = G(K, L, M, J)

    l = 0
    for k in range(0, 16):
        message = ""
        for m in range(l, l + 32):  # prepares the message
            message += temp[m]
        l += 32
        message = int(message, 2)
        M = (M + message) % pow(2, 32)
        J = H(K, L, M, J)

    l = 0
    for k in range(0, 16):
        message = ""
        for m in range(l, l + 32):  # prepares the message
            message += temp[m]
        l += 32
        message = int(message, 2)
        M = (M + message) % pow(2, 32)
        K = I(K, L, M, J)

    end = str(J).replace("0x", "") + str(K).replace("0x", "") + str(L).replace("0x", "") + str(M).replace("0x", "")

    return int(end)

def handler(con, ip, port, user):
    global conn_list, data_list
    address = (ip, port)
    try:
        while True:
            mes = con.read(4096)
            mes = str(mes)[2:-1].split(" ")
            if mes[0] == "MSG":
                if not (mes[1] in conn_list.keys()):
                    con.write(bytes("CNT <user not online> \r\n", "utf-8"))
                else:
                    res = " ".join(mes[3:-1])
                    object_list[mes[1]].send(bytes(f"RELAY {mes[1]} {mes[2]} {res} \r\n", "utf-8"))
            elif mes[0] == "END":
                con.write(bytes("END <end accepted> \r\n", "utf-8"))
                try:
                    object_list[user].close()
                except:
                    pass
                object_list.pop(user)
                conn_list.pop(user)
                print(f"<{user} left>")
                break
    except ConnectionResetError:
        try:
            object_list[user].close()
        except:
            pass
        object_list.pop(user)
        conn_list.pop(user)
        print(f"<{user} left>")
    except ValueError:
        try:
            object_list[user].close()
        except:
            pass
        object_list.pop(user)
        conn_list.pop(user)
        print(f"<{user} left>")
    except OSError:
        for k, v in object_list.items():
            try:
                v.close()
            except:
                pass
        print("<server closing>")
        exit()

def check():
    while True:
        time.sleep(60)
        for k, v in object_list.items():
            try:
                v.write(bytes("CHECK", "utf-8"))
            except:
                try:
                    v.close()
                except:
                    pass
                object_list.pop(k)





try:
    with open("user.csv", "r") as file:
        lines = file.readlines()
        f = {k.split(",")[0]: k.split(",")[1].replace("\n", "") for k in lines}
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain("cert.pem", "cert.pem")
        context.verify_mode &= ~ssl.CERT_REQUIRED

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(("192.168.1.26", 18443))
            server.listen(5)

            with context.wrap_socket(server, server_side=True) as secure_server:
                threading.Thread(target=check).start()
                while True:
                    conn, addr = secure_server.accept()

                    mes = conn.read(4096)
                    mes = str(mes)[2:-1].split(" ")
                    if not (mes[0] == "AUTH"):
                        conn.write(bytes("END * <incorrect protocol> \r\n", "utf-8"))
                        conn.close()
                    elif not f[mes[1]] == str(hash(mes[2])):
                        print(f[mes[1]])
                        print(hash(mes[2]))
                        conn.write(bytes("END <incorrect username or password> \r\n", "utf-8"))
                        conn.close()
                    elif mes[1] in object_list.keys():
                        conn.write(bytes("END <user already online> \r\n", "utf-8"))
                        conn.close()
                    else:
                        conn.write(bytes(f"ACCEPT {mes[1]} \r\n", "utf-8"))
                        print(f"<{mes[1]} accepted>")
                        conn_list[mes[1]] = threading.Thread(target=handler, args=[conn, addr[0], addr[1], mes[1]])
                        object_list[mes[1]] = conn
                        conn_list[mes[1]].start()
except:
    for k, v in object_list.items():
        try:
            v.close()
        except:
            pass




