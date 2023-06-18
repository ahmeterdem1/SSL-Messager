import socket
import ssl
import threading
import time
import sys

address = ("192.168.1.26", 18443)
flag = True
check = True
target = 0

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

def receiver(sock):
    global flag
    while True:
        try:
            m = sock.read(4096)
            m = str(m)[2:-1].split(" ")
            if m[0] == "RELAY":
                res = " ".join(m[3:-1])
                res = res[:-3]
                print()
                date = time.asctime()
                date = date.split(" ")
                date = " ".join(date[1:-1])
                print(f"> {m[2]}: {res} -- {date}")
            elif m[0] == "CNT":
                res = " ".join(m[1:-1])
                print()
                print(f"{res}")
            elif m[0] == "END":
                print()
                print("<connection closing>")
                flag = False
                break
        except ConnectionResetError:
            pass
        except ValueError:
            print("<server closed>")
            break
        except OSError:
            print("<program ending>")
            break

context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.load_cert_chain("certc.pem", "certc.pem")
context.check_hostname = False
context.verify_mode &= ~ssl.CERT_REQUIRED

try:
    with socket.create_connection(address) as out:
        with context.wrap_socket(out, server_hostname="192.168.1.26") as s:
            try:
                while True:
                    if check:
                        username = input("Username: ")
                        password = input("Password: ").replace('\n', '')
                    s.write(bytes(f"AUTH {username} {password} \r\n", "utf-8"))
                    mes = s.read(4096)
                    mes = str(mes)[2:-1].split(" ")
                    if mes[0] == "END" and mes[1] == "*":
                        res = " ".join(mes[2:-1])
                        print(res)
                        flag = False
                    elif mes[0] == "END" and mes[1] != "*":
                        res = " ".join(mes[1:-1])
                        print(res)
                        flag = False
                        check = True
                    elif mes[0] == "ACCEPT":
                        print("<log in complete>")

                    if flag:
                        threading.Thread(target=receiver, args=[s]).start()
                        target = input("Input the target: ")

                    while flag:
                        print("Enter your message:", end=" ")
                        message = sys.stdin.readline(2048)
                        if flag:
                            s.write(bytes(f"MSG {target} {username} {str(message)} \r\n", "utf-8"))
            except OSError:
                print()
                print("<program ended>")
                s.close()
                exit()
            except KeyboardInterrupt:
                print()
                print("<quiting>")
                s.close()
                exit()
except ConnectionRefusedError:
    print("<server not online>")
    exit()
