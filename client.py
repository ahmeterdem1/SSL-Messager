import socket
import ssl
import threading
import time
import sys
import signal
import os

address = ("192.168.1.6", 18443)
flag = True
check = True
target = 0
thread = 0
reset = False
token = 0
new_thread = True
put = False
group = False #group chat
down = False

if os.name == "nt":
    os.system("color")

command_list = ["quit", "online", "new_target", "toggle", "upload", "download", "status"]
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

def receiver(sock):
    global flag, thread, reset, check, new_thread, down
    thread = threading.get_ident()
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
            elif m[0] == "RELAYG":
                res = " ".join(m[2:-1])
                res = res[:-3]
                print()
                date = time.asctime()
                date = date.split(" ")
                date = " ".join(date[1:-1])
                print(f"\x1b[6;30;42mgroup> {m[1]}: {res} -- {date} \x1b[0m")
            elif m[0] == "CNT":
                res = " ".join(m[1:-1])
                print()
                print(f"{res}")
                flag = False
                reset = True
                check = False
                new_thread = True
                print("Press Enter to continue")
                break
            elif m[0] == "CMD":
                res = " ".join(m[1:-1])
                print()
                print(f"{res}")
            elif m[0] == "END" and m[1] != "*":  # after server sends this message, it closes its socket
                res = " ".join(m[1:-1])
                print()
                print(f"\033[91m {res} \x1b[0m")
                flag = False
                break
            elif m[0] == "END" and m[1] == "*":
                res = " ".join(m[2:-1])
                print()
                print(f"\033[91m {res} \x1b[0m")
                flag = False
                break
            elif m[0] == "CHECK":
                continue
            elif m[0] == "BEGIN":
                amount = int(m[1])
                down = True
                for k in range(amount):
                    new_file = sock.read(4096)
                    new_file = str(new_file)[2:-1].split(" ")
                    name = new_file[1]
                    begin = time.time()
                    with open(name, "xb") as save:
                        while True:
                            data = sock.read(4096 * 4096)
                            end = time.time()
                            control_data = str(data)[2:-1].split(" ")
                            if control_data[0] == "ENDF":
                                break
                            elif end - begin > 5:
                                break
                            save.write(data)
                down = False
            elif m[0] == "ENDF" or m[0] == "BEGINF":
                continue
        except ConnectionResetError:
            pass
        except ValueError:
            print("\033[91m <server closed> \x1b[0m")
            break
        except OSError:
            print("\033[91m <program ending> \x1b[0m")
            break

context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.load_cert_chain("../certc.pem", "../certc.pem")
context.check_hostname = False
context.verify_mode &= ~ssl.CERT_REQUIRED

try:
    with socket.create_connection(address, timeout=30) as out:
        with context.wrap_socket(out, server_hostname="192.168.1.6") as s:
            try:
                choice = input("Sign up, y/n?: ")
                if choice.lower() == "y":
                    put = True
                while True:
                    if not put:
                        if check:
                            username = input("Username: ")
                            password = input("Password: ").replace('\n', '')
                            s.write(bytes(f"AUTH {username} {password} \r\n", "utf-8"))
                            mes = s.read(4096)
                            mes = str(mes)[2:-1].split(" ")
                            if mes[0] == "END" and mes[1] == "*":
                                res = " ".join(mes[2:-1])
                                print(res)
                                break
                            elif mes[0] == "END" and mes[1] != "*":
                                res = " ".join(mes[1:-1])
                                print(res)
                                flag = False
                                check = True
                            elif mes[0] == "ACCEPT":
                                token = mes[-2]
                                print("<log in complete>")
                        if not check:
                            flag = True

                        if flag:
                            if new_thread:
                                threading.Thread(target=receiver, args=[s]).start()
                            target = input("Input the target: ")
                            reset = False

                        while flag:
                            print("Enter your message:", end=" ")
                            message = sys.stdin.readline(2048)
                            try:
                                if str(message)[0] == ":":
                                    command = str(message).split(":")[1]
                                    if command in command_list:

                                        if command == "quit":
                                            s.write(bytes(f"END <user command> {str(token)} \r\n", "utf-8"))
                                            raise KeyboardInterrupt  # I kinda cheat my way into quitting the program

                                        elif command == "online":
                                            s.write(bytes(f"CMD <online> {str(token)} \r\n", "utf-8"))

                                        elif command == "new_target":
                                            flag = False
                                            reset = True
                                            check = False
                                            new_thread = False

                                        elif command == "toggle":
                                            group = not group
                                            s.write(bytes(f"CMD <group> {token} \r\n", "utf-8"))

                                        elif command == "upload":
                                            path = input("Enter the file path: ")
                                            try:
                                                with open(path, "rb") as up:
                                                    upload = up.read()
                                                    if os.name == "nt" and "\\" in path:
                                                        extension = path.split("\\")[-1]
                                                    elif "/" in path:
                                                        extension = path.split("/")[-1]
                                                    else:
                                                        extension = path
                                                    s.write(bytes(f"BEGINF {extension} {target} {str(token)} \r\n", "utf-8"))
                                                    s.write(upload)
                                                    time.sleep(5)
                                                    s.write(bytes(f"ENDF {token} \r\n", "utf-8"))
                                            except:
                                                print("A problem has occured, try again.")

                                        elif command == "download":
                                            s.write(bytes(f"CMD <get> {token} \r\n", "utf-8"))
                                            while True:
                                                time.sleep(0.1)
                                                if not down:
                                                    break
                                        elif command == "status":
                                            print(f"Target: {target}")
                                            print(f"Group: {group}")

                                    else:
                                        if flag and not group:
                                            s.write(bytes(f"MSG {target} {username} {str(message)} {str(token)} \r\n", "utf-8"))
                                        elif flag and group:
                                            s.write(bytes(f"MSGG {username} {str(message)} {str(token)} \r\n", "utf-8"))
                                        if reset:
                                            break
                                else:
                                    if flag and not group:
                                        s.write(bytes(f"MSG {target} {username} {str(message)} {str(token)} \r\n", "utf-8"))
                                    elif flag and group:
                                        s.write(bytes(f"MSGG {username} {str(message)} {str(token)} \r\n", "utf-8"))

                                    if reset:
                                        break
                            except IndexError:
                                raise KeyboardInterrupt
                    else:
                        if check:
                            flag = False
                            username = input("Username: ")
                            password = input("Password: ").replace('\n', '')
                            s.write(bytes(f"PUT {username} {password} \r\n", "utf-8"))
                            mes = s.read(4096)
                            mes = str(mes)[2:-1].split(" ")
                            if mes[0] == "TRY":
                                res = " ".join(mes[1:-1])
                                print()
                                print(res)
                                continue
                            elif mes[0] == "END":
                                res = " ".join(mes[1:-1])
                                print()
                                print(res)
                                raise KeyboardInterrupt
                            elif mes[0] == "ACCEPT":
                                token = mes[-2]
                                print("<log in complete>")
                                check = False
                        if not check:
                            flag = True

                        if flag:
                            if new_thread:
                                threading.Thread(target=receiver, args=[s]).start()
                            target = input("Input the target: ")
                            reset = False

                        while flag:
                            print("Enter your message:", end=" ")
                            message = sys.stdin.readline(2048)
                            try:
                                if str(message)[0] == ":":
                                    command = str(message).split(":")[1]
                                    if command in command_list:

                                        if command == "quit":
                                            s.write(bytes(f"END <user command> {str(token)} \r\n", "utf-8"))
                                            raise KeyboardInterrupt

                                        elif command == "online":
                                            s.write(bytes(f"CMD <online> {str(token)} \r\n", "utf-8"))

                                        elif command == "new_target":
                                            flag = False
                                            reset = True
                                            check = False
                                            new_thread = False

                                        elif command == "toggle":
                                            group = not group
                                            s.write(bytes(f"CMD <group> {token} \r\n", "utf-8"))

                                        elif command == "upload":
                                            path = input("Enter the file path: ")
                                            try:
                                                with open(path, "rb") as up:
                                                    upload = up.read()
                                                    if os.name == "nt" and "\\" in path:
                                                        extension = path.split("\\")[-1]
                                                    elif "/" in path:
                                                        extension = path.split("/")[-1]
                                                    else:
                                                        extension = path
                                                    s.write(bytes(f"BEGINF {extension} {target} {str(token)} \r\n", "utf-8"))
                                                    s.write(upload)
                                                    time.sleep(5)
                                                    s.write(bytes(f"ENDF {token} \r\n", "utf-8"))
                                            except:
                                                print("A problem has occured, try again.")

                                        elif command == "download":
                                            s.write(bytes(f"CMD <get> {token} \r\n", "utf-8"))
                                            while True:
                                                time.sleep(0.1)
                                                if not down:
                                                    break
                                        elif command == "status":
                                            print(f"Target: {target}")
                                            print(f"Group: {group}")

                                    else:
                                        if flag and not group:
                                            s.write(bytes(f"MSG {target} {username} {str(message)} {str(token)} \r\n", "utf-8"))
                                        elif flag and group:
                                            s.write(bytes(f"MSGG {username} {str(message)} {str(token)} \r\n", "utf-8"))

                                        if reset:
                                            break
                                else:
                                    if flag and not group:
                                        s.write(bytes(f"MSG {target} {username} {str(message)} {str(token)} \r\n", "utf-8"))
                                    elif flag and group:
                                        s.write(bytes(f"MSGG {username} {str(message)} {str(token)} \r\n", "utf-8"))
                                    if reset:
                                        break
                            except IndexError:
                                raise KeyboardInterrupt


            except OSError:
                print()
                print("<program ended>")
                flag = False
                reset = True
                if os.name != "nt":
                    try:
                        signal.pthread_kill(thread, signal.SIGKILL)
                    except:
                        pass
                s.close()
            except KeyboardInterrupt:
                print()
                print("<quiting>")
                flag = False
                reset = True
                if os.name != "nt":
                    try:
                        signal.pthread_kill(thread, signal.SIGKILL)
                    except:
                        pass
                s.close()
            except Exception as e:
                print(f"An unexpected error has occured: {e}")
                print("<quiting>")
                flag = False
                reset = True
                if os.name != "nt":
                    try:
                        signal.pthread_kill(thread, signal.SIGKILL)
                    except:
                        pass
                s.close()


except ConnectionRefusedError:
    print("<server not online>")
    sys.exit()
except socket.timeout:
    print("<connection timeout - check your internet connection>")
    sys.exit()
except ssl.SSLError:
    print("<TLS connection error>")
    sys.exit()
except Exception as e:
    print(f"An unexpected error has occured: {e}")
    sys.exit()

