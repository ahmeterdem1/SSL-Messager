import socket
import ssl
import sys
import time
import threading
import signal

#configuration
#192.168.1.15
#13.50.8.62
address = ("13.50.8.62", 18443)
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.load_cert_chain("../certc.pem", "../certc.pem")
context.check_hostname = False
context.verify_mode &= ~ssl.CERT_REQUIRED
id = 0

#connection
def connect():
    try:
        with socket.create_connection(address, timeout=30) as out:
            with context.wrap_socket(out, server_hostname="13.50.8.62") as s:
                while True:
                    print("Enter your query:")
                    q = sys.stdin.readline(4096)
                    wbegin = time.time_ns()
                    s.write(bytes(q, "utf-8"))
                    wend = time.time_ns()
                    # we will not support receiving files here
                    threading.Thread(target=read, args=[s]).start()
                    """rbegin = time.time_ns()
                    res = s.recv(4096)
                    rend = time.time_ns()
                    print("Response")
                    print(str(res)[2:-1])
                    print(f"Write time {wend - wbegin}ns")
                    print(f"Read time {rend - rbegin}ns")"""
                    print("---------")
    except Exception as e:
        print(f"An error has occured: {e}")
        print("Starting again.")
        try:
            signal.pthread_kill(id, signal.SIGKILL)
        except:
            pass
        return connect()

def read(con):
    global id
    id = threading.get_ident()
    try:
        while True:
            rbegin = time.time_ns()
            res = con.recv(4096)
            rend = time.time_ns()
            print("Response")
            print(str(res)[2:-1])
            print(f"Read time {rend - rbegin}ns")
            if str(res)[2:5] == "END":
                break
    except:
        return


if __name__ == "__main__":
    connect()


