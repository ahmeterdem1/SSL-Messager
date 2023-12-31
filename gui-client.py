import socket, ssl, os, threading
from random import choice
if os.name == "posix":
    from signal import pthread_kill, SIGKILL
from time import asctime, sleep
from sys import argv
from PySide6.QtWidgets import QApplication, QPushButton, QLabel, QWidget, \
    QVBoxLayout, QMessageBox, QTabWidget, QHBoxLayout, \
    QLineEdit, QScrollArea
from PySide6.QtCore import Qt
from playsound import playsound
import xml.etree.ElementTree as ET

# external configurations
address = ("", 0)
timeout = None
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
#context.load_cert_chain("../certc.pem", "../certc.pem")
context.check_hostname = False
context.verify_mode &= ~ssl.CERT_REQUIRED

username = ""
password = ""
program_allowed = False
token = 0
target = ""
mute_list = list()
up_permit = False
not_permitted = False
down = False
#file_sent = False


def file_gen(file):
    while True:
        data = file.read(4096)
        if len(data) == 0:
            break
        yield data


"""def file_sender(main, number, file, number_of_packets):
    global file_sent
    for data in file_gen(file):
        main.socket.write(data)
        number += 1
        if not number % 10:
            percentage = (number / number_of_packets) * 100
            print(percentage)
            main.status.setText(f"{percentage:.2f}%")
    main.socket.write(bytes(f"ENDF {main.token} \r\n", "utf-8"))
    file_sent = True"""

class Entry(QWidget):
    """
    This class is for logging in and signing up, nothing more.
    """
    def __init__(self, sock: ssl.SSLSocket, sign_up: bool):
        super().__init__()
        self.resend_allowed = True
        self.quit_button = QPushButton()
        self.quit_button.clicked.connect(self.exit)

        self.socket = sock
        self.send = QPushButton("Enter the chat")
        self.send.setStyleSheet("background: lightgreen; color: black; border-radius: 3px; height: 20px; width: 130px;")
        self.send.clicked.connect(self.auth)
        self.put = sign_up
        self.info = QLabel("")

        general_layout = QVBoxLayout()
        sub_layout1 = QHBoxLayout()
        sub_widget1 = QWidget()
        sub_layout2 = QHBoxLayout()
        sub_widget2 = QWidget()
        sub_layout3 = QHBoxLayout()
        sub_widget3 = QWidget()

        self.username = QLineEdit()
        self.username.returnPressed.connect(self.auth)
        sub_layout1.addWidget(QLabel("Username: "))
        sub_layout1.addWidget(self.username)
        sub_widget1.setLayout(sub_layout1)

        self.password = QLineEdit()
        self.password.returnPressed.connect(self.auth)
        sub_layout2.addWidget(QLabel("Password: "))
        sub_layout2.addWidget(self.password)
        sub_widget2.setLayout(sub_layout2)

        self.target = QLineEdit()
        self.target.returnPressed.connect(self.auth)
        sub_layout3.addWidget(QLabel("Target: "))
        sub_layout3.addWidget(self.target)
        sub_widget3.setLayout(sub_layout3)

        general_layout.addWidget(sub_widget1)
        general_layout.addWidget(sub_widget2)
        general_layout.addWidget(sub_widget3)
        general_layout.addWidget(self.info)
        general_layout.addWidget(self.send)
        self.setLayout(general_layout)


    def auth(self):
        global username, password
        username = self.username.text()
        password = self.password.text()
        # so that server does not break down by receiving empty username and passwords
        if username == "":
            username = "*"
        if password == "":
            password = "*"
        if self.put and self.resend_allowed:
            self.socket.write(bytes(f"PUT {username} {password} \r\n", "utf-8"))
        elif self.resend_allowed:
            self.socket.write(bytes(f"AUTH {username} {password} \r\n", "utf-8"))

    def exit(self):
        try:
            self.socket.write(bytes(f"CMD <group> {token} \r\n", "utf-8"))
        except:
            pass
        self.close()


class Widget(QWidget):
    """
    This is the main window of the program. Everything happens here.
    """
    def __init__(self, sock: ssl.SSLSocket):
        super().__init__()
        self.socket = sock
        self.token = 0
        self.target = target
        self.username = ""
        self.change_target = False
        self.private_label_amount = 0
        self.group_label_amount = 0
        self.mute_function = False
        self.unmute_function = False
        self.upload_function = False
        self.download_function = False
        self.function_list = [self.change_target, self.mute_function, self.unmute_function, self.upload_function, self.download_function]
        self.upload_started = False
        self.download_started = False
        self.the_other_thread = 0

        self.send_setting = "background: lime; color: black; border-radius: 3px; height: 20px; width: 50px;"
        self.color_list = ("red", "pink", "green", "lightgreen", "aqua", "yellow", "orange",
                           "purple", "bisque", "cornflowerblue", "crimson", "lightcoral")
        self.users = dict()
        # :online: could be carried to client side only in the future thanks to this.
        # Only difference would be that, for this list to be filled, the user must have messaged you.

        self.meme_list = {":bruh:": "../ssl-emoji/bruh.jpeg", ":hm:": "../ssl-emoji/hm.jpeg",
                          ":swag:": "../ssl-emoji/swag.jpeg", ":eee:": "../ssl-emoji/eee.jpeg",
                          ":iii:": "../ssl-emoji/iii.jpeg", ":ohom:": "../ssl-emoji/ohom.jpeg"}
        if os.name == "nt":
            self.meme_list = {":bruh:": r"..\ssl-emoji\bruh.jpeg", ":hm:": r"..\ssl-emoji\hm.jpeg",
                              ":swag:": r"..\ssl-emoji\swag.jpeg", ":eee:": r"..\ssl-emoji\eee.jpeg",
                              ":iii:": r"..\ssl-emoji\iii.jpeg", ":ohom:": r"..\ssl-emoji\ohom.jpeg"}
        # You may change here. Effects will be obviously only on you.

        self.error_received_trigger = QPushButton()
        self.error_received_trigger.clicked.connect(self.error_received)
        self.error_info = ""
        self.error_explanation = ""

        self.private_received_trigger = QPushButton()
        self.private_received_trigger.clicked.connect(self.private_received)
        self.private_who = ""
        self.private_what = ""

        self.group_received_trigger = QPushButton()
        self.group_received_trigger.clicked.connect(self.group_received)
        self.group_who = ""
        self.group_what = ""

        tabs = QTabWidget(self)
        general_layout = QVBoxLayout()
        self.status = QLabel("")
        self.status.setStyleSheet("font-style: italic;")
        self.status_group = QLabel("")

        self.quit_button = QPushButton("Quit")
        self.quit_button.setStyleSheet("background: red; color: black; border-radius: 3px; height: 20px; width: 50px;")
        self.quit_button.clicked.connect(self.quit)

        self.online_button = QPushButton("Online")
        self.online_button.setStyleSheet("background: orange; color: black; border-radius: 3px; height: 20px; width: 70px;")
        self.online_button.clicked.connect(self.online)

        self.new_target_button = QPushButton("New Target")
        self.new_target_button.setStyleSheet("background: orange; color: black; border-radius: 3px; height: 20px; width: 100px;")
        self.new_target_button.clicked.connect(self.new_target)

        self.upload_button = QPushButton("Upload")
        self.upload_button.setStyleSheet("background: orange; color: black; border-radius: 3px; height: 20px; width: 70px;")
        self.upload_button.clicked.connect(self.upload)

        self.download_button = QPushButton("Download")
        self.download_button.setStyleSheet("background: orange; color: black; border-radius: 3px; height: 20px; width: 80px;")
        self.download_button.clicked.connect(self.download)

        self.help_button = QPushButton("Help")
        self.help_button.setStyleSheet("background: orange; color: black; border-radius: 3px; height: 20px; width: 40px;")
        self.help_button.clicked.connect(self.help)

        self.mute_button = QPushButton("Mute")
        self.mute_button.setStyleSheet("background: orange; color: black; border-radius: 3px; height: 20px; width: 40px;")
        self.mute_button.clicked.connect(self.mute)

        self.unmute_button = QPushButton("Unmute")
        self.unmute_button.setStyleSheet("background: orange; color: black; border-radius: 3px; height: 20px; width: 70px;")
        self.unmute_button.clicked.connect(self.unmute)



        self.quit_button_group = QPushButton("Quit")
        self.quit_button_group.setStyleSheet("background: red; color: black; border-radius: 3px; height: 20px; width: 50px;")
        self.quit_button_group.clicked.connect(self.quit)

        self.online_button_group = QPushButton("Online")
        self.online_button_group.setStyleSheet("background: orange; color: black; border-radius: 3px; height: 20px; width: 70px;")
        self.online_button_group.clicked.connect(self.online)

        self.new_target_button_group = QPushButton("New Target")
        self.new_target_button_group.setStyleSheet("background: orange; color: black; border-radius: 3px; height: 20px; width: 100px;")
        self.new_target_button_group.clicked.connect(self.new_target)

        self.upload_button_group = QPushButton("Upload")
        self.upload_button_group.setStyleSheet("background: orange; color: black; border-radius: 3px; height: 20px; width: 70px;")
        self.upload_button_group.clicked.connect(self.upload)

        self.download_button_group = QPushButton("Download")
        self.download_button_group.setStyleSheet("background: orange; color: black; border-radius: 3px; height: 20px; width: 80px;")
        self.download_button_group.clicked.connect(self.download)

        self.help_button_group = QPushButton("Help")
        self.help_button_group.setStyleSheet("background: orange; color: black; border-radius: 3px; height: 20px; width: 40px;")
        self.help_button_group.clicked.connect(self.help)

        self.mute_button_group = QPushButton("Mute")
        self.mute_button_group.setStyleSheet("background: orange; color: black; border-radius: 3px; height: 20px; width: 40px;")
        self.mute_button_group.clicked.connect(self.mute)

        self.unmute_button_group = QPushButton("Unmute")
        self.unmute_button_group.setStyleSheet("background: orange; color: black; border-radius: 3px; height: 20px; width: 70px;")
        self.unmute_button_group.clicked.connect(self.unmute)


        #  Globals for private chat tab
        self.private_messages_layout = QVBoxLayout()
        self.private_messages_widget = QWidget()
        self.private_edit = QLineEdit()
        self.private_edit.returnPressed.connect(self.send)
        self.private_send = QPushButton("Send")
        self.private_send.setStyleSheet(self.send_setting)
        self.private_send.clicked.connect(self.send)

        #  Globals for group chat
        self.group_messages_layout = QVBoxLayout()
        self.group_messages_widget = QWidget()
        self.group_edit = QLineEdit()
        self.group_edit.returnPressed.connect(self.sendg)
        self.group_send = QPushButton("Send")
        self.group_send.setStyleSheet(self.send_setting)
        self.group_send.clicked.connect(self.sendg)

        #  Private chat setup
        private_chat = QWidget()
        private_chat_layout = QVBoxLayout()



        commands_widget = QWidget()
        commands_layout = QHBoxLayout()
        commands_layout.addWidget(self.quit_button)
        commands_layout.addWidget(self.online_button)
        commands_layout.addWidget(self.new_target_button)
        commands_layout.addWidget(self.upload_button)
        commands_layout.addWidget(self.download_button)
        commands_layout.addWidget(self.help_button)
        commands_layout.addWidget(self.mute_button)
        commands_layout.addWidget(self.unmute_button)
        commands_layout.addWidget(self.status)
        commands_widget.setLayout(commands_layout)

        self.private_scroll = QScrollArea()
        self.private_scroll.setStyleSheet("background: black;")
        self.private_messages_widget.setLayout(self.private_messages_layout)

        self.private_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.private_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.private_scroll.setWidgetResizable(True)
        self.private_scroll.setWidget(self.private_messages_widget)

        private_bottom_widget = QWidget()
        private_bottom_layout = QHBoxLayout()
        private_bottom_layout.addWidget(self.private_edit)
        private_bottom_layout.addWidget(self.private_send)
        private_bottom_widget.setLayout(private_bottom_layout)

        private_chat_layout.addWidget(commands_widget)
        private_chat_layout.addWidget(self.private_scroll)
        private_chat_layout.addWidget(private_bottom_widget)
        private_chat.setLayout(private_chat_layout)



        # Group chat setup

        group_chat = QWidget()
        group_chat_layout = QVBoxLayout()

        # Important note that, these buttons are the same as private chat ones
        # Their action will be the same, and this is intended
        commands_group_widget = QWidget()
        commands_group_layout = QHBoxLayout()
        commands_group_layout.addWidget(self.quit_button_group)
        commands_group_layout.addWidget(self.online_button_group)
        commands_group_layout.addWidget(self.new_target_button_group)
        commands_group_layout.addWidget(self.upload_button_group)
        commands_group_layout.addWidget(self.download_button_group)
        commands_group_layout.addWidget(self.help_button_group)
        commands_group_layout.addWidget(self.mute_button_group)
        commands_group_layout.addWidget(self.unmute_button_group)
        commands_group_layout.addWidget(self.status_group)

        commands_group_widget.setLayout(commands_group_layout)

        self.group_scroll = QScrollArea()
        self.group_scroll.setStyleSheet("background: black;")
        self.group_messages_widget.setLayout(self.group_messages_layout)

        self.group_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.group_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.group_scroll.setWidgetResizable(True)
        self.group_scroll.setWidget(self.group_messages_widget)

        group_bottom_widget = QWidget()
        group_bottom_layout = QHBoxLayout()
        group_bottom_layout.addWidget(self.group_edit)
        group_bottom_layout.addWidget(self.group_send)
        group_bottom_widget.setLayout(group_bottom_layout)

        group_chat_layout.addWidget(commands_group_widget)
        group_chat_layout.addWidget(self.group_scroll)
        group_chat_layout.addWidget(group_bottom_widget)
        group_chat.setLayout(group_chat_layout)


        tabs.addTab(private_chat, "Private")
        tabs.addTab(group_chat, "Group")
        general_layout.addWidget(tabs)
        self.setLayout(general_layout)
        self.setFixedSize(850, 640)


    # The slot
    def quit(self):
        """
        Same as :quit:
        :return: None
        """
        if program_allowed and not self.upload_function and not self.download_function:
            self.socket.write(bytes(f"END {self.token} \r\n", "utf-8"))
            try:
                if os.name == "posix":
                    pthread_kill(self.the_other_thread, SIGKILL)
            except:
                pass
            self.close()
        elif self.upload_function or self.download_function:
            QMessageBox.information(self, "Wait", "Wait until FTP action ends", QMessageBox.StandardButton.Ok)
            # Yeah they can still forcefully quit
        else:
            QMessageBox.information(self, "Log in", "Finalize logging in first", QMessageBox.StandardButton.Ok)

    def online(self):
        """
        Same as :online:
        :return: None
        """
        if program_allowed and not self.upload_function and not self.download_function:
            self.socket.write(bytes(f"CMD <online> {self.token} \r\n", "utf-8"))
        elif self.upload_function or self.download_function:
            QMessageBox.information(self, "Wait", "Wait until FTP action ends", QMessageBox.StandardButton.Ok)
        else:
            QMessageBox.information(self, "Log in", "Finalize logging in first", QMessageBox.StandardButton.Ok)

    def new_target(self):
        """
        Same as :new_target:
        :return: None
        """
        if program_allowed:
            for k in self.function_list:
                k = False
            self.change_target = True
            QMessageBox.information(self, "Change Target", "Input the new target in the text area below", QMessageBox.StandardButton.Ok)
            self.private_send.setText("Change Target")
            self.private_send.setStyleSheet("background: lime; color: black; border-radius: 3px; height: 20px; width: 100px;")
            self.group_send.setText("Change Target")
            self.group_send.setStyleSheet("background: lime; color: black; border-radius: 3px; height: 20px; width: 100px;")
        else:
            QMessageBox.information(self, "Log in", "Finalize logging in first", QMessageBox.StandardButton.Ok)

    def send(self):
        """
        Sends messages, connected to the private chat tab.
        :return: None
        """
        global mute_list, file_sent
        if program_allowed and not self.change_target and not self.mute_function \
                and not self.unmute_function and not self.upload_function and not self.download_function:

            message = self.private_edit.text()
            if len(message) > 4000:
                QMessageBox.information(self, "Too Long", "Your message exceeds 4000 character limit.", QMessageBox.StandardButton.Ok)
                return

            message = message.replace("ı", "i").replace("İ", "I").replace("ü", "u").replace("Ü", "U")
            message = message.replace("ö", "o").replace("Ö", "O").replace("ğ", "g").replace("Ğ", "G").replace("ş", "s")
            message = message.replace("Ş", "S").replace("ç", "c").replace("Ç", "C")

            self.socket.write(bytes(f"MSG {self.target} {self.username} {message} {self.token} \r\n", "utf-8"))

            date = asctime()
            date = date.split(" ")
            date = " ".join(date[1:-1])

            for k, v in self.meme_list.items():
                if os.path.exists(v):
                    message = message.replace(k, f"<img src='{v}'>")

            if "_" in message:
                to_work = message.split("_")
                length = len(to_work)
                if length > 2:
                    for k in range(length):
                        if k % 2 == 1 and not k == length - 1:
                            to_work[k] = f"<em>{to_work[k]}</em>"
                        elif k == length - 1 and length % 2 == 0:
                            to_work[k] = f"_{to_work[k]}"
                    message = "".join(to_work)
            if "*" in message:
                to_work = message.split("*")
                length = len(to_work)
                if length > 2:
                    for k in range(length):
                        if k % 2 == 1 and not k == length - 1:
                            to_work[k] = f"<b>{to_work[k]}</b>"
                        elif k == length - 1 and length % 2 == 0:
                            to_work[k] = f"*{to_work[k]}"
                    message = "".join(to_work)

            your_text = f"You> {message} -- {date}"
            self.private_messages_layout.addWidget(QLabel(your_text))
            self.private_label_amount += 1
            self.private_edit.setText("")
            self.private_scroll.verticalScrollBar().setValue(2000 * self.private_label_amount)

        elif not program_allowed:
            QMessageBox.information(self, "Log in", "Finalize logging in first", QMessageBox.StandardButton.Ok)

        elif self.change_target:
            self.target = self.private_edit.text()
            self.status.setText(self.target)
            self.status_group.setText(self.target)
            self.private_send.setText("Send")
            self.private_send.setStyleSheet(self.send_setting)
            self.group_send.setText("Send")
            self.group_send.setStyleSheet(self.send_setting)
            self.private_edit.setText("")
            self.group_edit.setText("")
            self.change_target = False

        elif self.mute_function:
            username_list = self.private_edit.text().split(" ")
            if "" in username_list:
                QMessageBox.information(self, "Typo", "Incorrect format for username list", QMessageBox.StandardButton.Ok)
                self.mute_function = False
                self.private_send.setText("Send")
                self.private_send.setStyleSheet(self.send_setting)
                self.group_send.setText("Send")
                self.group_send.setStyleSheet(self.send_setting)
                self.private_edit.setText("")
                self.group_edit.setText("")
            else:
                for k in username_list:
                    if k not in mute_list and k != "admin":
                        mute_list.append(k)
                QMessageBox.information(self, "Muted", "Users muted", QMessageBox.StandardButton.Ok)
                self.mute_function = False
                self.private_send.setText("Send")
                self.private_send.setStyleSheet(self.send_setting)
                self.group_send.setText("Send")
                self.group_send.setStyleSheet(self.send_setting)
                self.private_edit.setText("")
                self.group_edit.setText("")

        elif self.unmute_function:
            username_list = self.private_edit.text().split(" ")
            if "" in username_list:
                QMessageBox.information(self, "Typo", "Incorrect format for username list",
                                        QMessageBox.StandardButton.Ok)
                self.unmute_function = False
                self.private_send.setText("Send")
                self.private_send.setStyleSheet(self.send_setting)
                self.group_send.setText("Send")
                self.group_send.setStyleSheet(self.send_setting)
                self.private_edit.setText("")
                self.group_edit.setText("")
            else:
                for k in username_list:
                    if k in mute_list:
                        index = mute_list.index(k)
                        mute_list.pop(index)
                QMessageBox.information(self, "Unmuted", "Users unmuted", QMessageBox.StandardButton.Ok)
                self.unmute_function = False
                self.private_send.setText("Send")
                self.private_send.setStyleSheet(self.send_setting)
                self.group_send.setText("Send")
                self.group_send.setStyleSheet(self.send_setting)
                self.private_edit.setText("")
                self.group_edit.setText("")

        elif self.upload_function and not self.upload_started:
            path = self.private_edit.text()
            try:
                size = os.stat(path).st_size
                with open(path, "rb") as up:
                    #upload = up.read()
                    number_of_packets = (size // 4096) + 1
                    if os.name == "nt" and "\\" in path:
                        path = path.replace(" ", "_")
                        extension = path.split("\\")[-1]
                    elif "/" in path:
                        path = path.replace(" ", "_")
                        extension = path.split("/")[-1]
                    else:
                        path = path.replace(" ", "_")
                        extension = path
                    self.socket.write(bytes(f"BEGINF {extension} {self.target} {size} {self.token} \r\n", "utf-8"))
                    tout = 0

                    while (tout < 1500 and not up_permit) and not not_permitted:
                        sleep(0.01)
                        tout += 1

                    if up_permit:
                        self.upload_started = True
                        self.socket.settimeout(None)
                        n = 0
                        """th = threading.Thread(target=file_sender, args=[self, n, up, number_of_packets])
                        th.start()"""
                        """while not file_sent:
                            sleep(0.05)"""
                        #file_sent = False
                        #th.join()
                        for data in file_gen(up):
                            self.socket.write(data)
                            n += 1
                            if not n % 10:
                                percentage = (n / number_of_packets) * 100
                                print(percentage)
                                #self.status.setText(f"{percentage:.2f}%")
                        #s.write(upload)
                        self.socket.write(bytes(f"ENDF {self.token} \r\n", "utf-8"))
                        #self.status.setText(self.target)
                        self.upload_started = False
                    else:
                        QMessageBox.information(self, "Upload", "Upload not permitted", QMessageBox.StandardButton.Ok)

                    self.upload_function = False
                    self.upload_started = False
                    self.private_send.setText("Send")
                    self.private_send.setStyleSheet(self.send_setting)
                    self.group_send.setText("Send")
                    self.group_send.setStyleSheet(self.send_setting)
                    self.private_edit.setText("")
                    self.group_edit.setText("")
            except Exception as e:
                self.upload_function = False
                self.upload_started = False
                QMessageBox.information(self, "Error", f"Error: {e}", QMessageBox.StandardButton.Ok)
                self.private_send.setText("Send")
                self.private_send.setStyleSheet(self.send_setting)
                self.group_send.setText("Send")
                self.group_send.setStyleSheet(self.send_setting)
                self.private_edit.setText("")
                self.group_edit.setText("")

    def sendg(self):
        """
        Sends messages, connected to the group chat tab.
        :return: None
        """
        if program_allowed and not self.change_target and not self.mute_function \
                and not self.unmute_function and not self.upload_function:

            message = self.group_edit.text()
            if len(message) > 4000:
                QMessageBox.information(self, "Too Long", "Your message exceeds 4000 character limit.", QMessageBox.StandardButton.Ok)
                return

            message = message.replace("ı", "i").replace("İ", "I").replace("ü", "u").replace("Ü", "U")
            message = message.replace("ö", "o").replace("Ö", "O").replace("ğ", "g").replace("Ğ", "G").replace("ş", "s")
            message = message.replace("Ş", "S").replace("ç", "c").replace("Ç", "C")

            self.socket.write(bytes(f"MSGG {self.username} {message} {self.token} \r\n", "utf-8"))
            self.group_label_amount += 1

            date = asctime()
            date = date.split(" ")
            date = " ".join(date[1:-1])

            for k, v in self.meme_list.items():
                if os.path.exists(v):
                    message = message.replace(k, f"<img src='{v}'>")

            if "_" in message:
                to_work = message.split("_")
                length = len(to_work)
                if length > 2:
                    for k in range(length):
                        if k % 2 == 1 and not k == length - 1:
                            to_work[k] = f"<em>{to_work[k]}</em>"
                        elif k == length - 1 and length % 2 == 0:
                            to_work[k] = f"_{to_work[k]}"
                    message = "".join(to_work)
            if "*" in message:
                to_work = message.split("*")
                length = len(to_work)
                if length > 2:
                    for k in range(length):
                        if k % 2 == 1 and not k == length - 1:
                            to_work[k] = f"<b>{to_work[k]}</b>"
                        elif k == length - 1 and length % 2 == 0:
                            to_work[k] = f"*{to_work[k]}"
                    message = "".join(to_work)

            your_text = f"You> {message} -- {date}"
            self.group_messages_layout.addWidget(QLabel(your_text))
            self.group_edit.setText("")
            self.group_scroll.verticalScrollBar().setValue(2000 * self.group_label_amount)

        elif not program_allowed:
            QMessageBox.information(self, "Log in", "Finalize logging in first", QMessageBox.StandardButton.Ok)

        elif self.change_target:
            self.target = self.group_edit.text()
            self.status.setText(self.target)
            self.status_group.setText(self.target)
            self.private_send.setText("Send")
            self.private_send.setStyleSheet(self.send_setting)
            self.group_send.setText("Send")
            self.group_send.setStyleSheet(self.send_setting)
            self.private_edit.setText("")
            self.group_edit.setText("")
            self.change_target = False

        elif self.mute_function:
            username_list = self.group_edit.text().split(" ")
            if "" in username_list:
                QMessageBox.information(self, "Typo", "Incorrect format for username list",
                                        QMessageBox.StandardButton.Ok)
                self.mute_function = False
                self.private_send.setText("Send")
                self.private_send.setStyleSheet(self.send_setting)
                self.group_send.setText("Send")
                self.group_send.setStyleSheet(self.send_setting)
                self.private_edit.setText("")
                self.group_edit.setText("")
            else:
                for k in username_list:
                    if k not in mute_list and k != "admin":
                        mute_list.append(k)
                QMessageBox.information(self, "Muted", "Users muted", QMessageBox.StandardButton.Ok)
                self.mute_function = False
                self.private_send.setText("Send")
                self.private_send.setStyleSheet(self.send_setting)
                self.group_send.setText("Send")
                self.group_send.setStyleSheet(self.send_setting)
                self.private_edit.setText("")
                self.group_edit.setText("")

        elif self.unmute_function:
            username_list = self.group_edit.text().split(" ")
            if "" in username_list:
                QMessageBox.information(self, "Typo", "Incorrect format for username list",
                                        QMessageBox.StandardButton.Ok)
                self.unmute_function = False
                self.private_send.setText("Send")
                self.private_send.setStyleSheet(self.send_setting)
                self.group_send.setText("Send")
                self.group_send.setStyleSheet(self.send_setting)
                self.private_edit.setText("")
                self.group_edit.setText("")
            else:
                for k in username_list:
                    if k in mute_list:
                        index = mute_list.index(k)
                        mute_list.pop(index)
                QMessageBox.information(self, "Unmuted", "Users unmuted", QMessageBox.StandardButton.Ok)
                self.unmute_function = False
                self.private_send.setText("Send")
                self.private_send.setStyleSheet(self.send_setting)
                self.group_send.setText("Send")
                self.group_send.setStyleSheet(self.send_setting)
                self.private_edit.setText("")
                self.group_edit.setText("")

        elif self.upload_function and not self.upload_started:
            path = self.group_edit.text()
            try:
                size = os.stat(path).st_size
                number_of_packets = (size // 4096) + 1
                with open(path, "rb") as up:
                    #upload = up.read()
                    if os.name == "nt" and "\\" in path:
                        path = path.replace(" ", "_")
                        extension = path.split("\\")[-1]
                    elif "/" in path:
                        path = path.replace(" ", "_")
                        extension = path.split("/")[-1]
                    else:
                        path = path.replace(" ", "_")
                        extension = path
                    self.socket.write(bytes(f"BEGINF {extension} {self.target} {size} {self.token} \r\n", "utf-8"))
                    tout = 0

                    while (tout < 1500 and not up_permit) and not not_permitted:
                        sleep(0.01)
                        tout += 1

                    if up_permit:
                        self.upload_started = True
                        self.socket.settimeout(None)
                        #s.write(upload)
                        n = 0
                        for data in file_gen(up):
                            self.socket.write(data)
                            n += 1
                            if not n % 10:
                                percentage = (n / number_of_packets) * 100
                                print(percentage)
                        s.write(bytes(f"ENDF {self.token} \r\n", "utf-8"))
                        self.upload_started = False
                    else:
                        QMessageBox.information(self, "Upload", "Upload not permitted", QMessageBox.StandardButton.Ok)

                    self.upload_function = False
                    self.upload_started = False
                    self.private_send.setText("Send")
                    self.private_send.setStyleSheet(self.send_setting)
                    self.group_send.setText("Send")
                    self.group_send.setStyleSheet(self.send_setting)
                    self.private_edit.setText("")
                    self.group_edit.setText("")
            except Exception as e:
                self.upload_function = False
                self.upload_started = False
                QMessageBox.information(self, "Error", f"Error: {e}", QMessageBox.StandardButton.Ok)
                self.private_send.setText("Send")
                self.private_send.setStyleSheet(self.send_setting)
                self.group_send.setText("Send")
                self.group_send.setStyleSheet(self.send_setting)
                self.private_edit.setText("")
                self.group_edit.setText("")

    def private_received(self):
        """
        Puts the received private messages on the screen.
        Triggered by an invisible button clicked by the receiver thread.
        :return: None
        """
        if program_allowed and self.private_who not in mute_list:
            self.private_label_amount += 1
            date = asctime()
            date = date.split(" ")
            date = " ".join(date[1:-1])
            # style preparations before displaying the message

            for k, v in self.meme_list.items():
                if os.path.exists(v):
                    self.private_what = self.private_what.replace(k, f"<img src='{v}'>")

            if "_" in self.private_what:
                to_work = self.private_what.split("_")
                length = len(to_work)
                if length > 2:
                    for k in range(length):
                        if k % 2 == 1 and not k == length - 1:
                            to_work[k] = f"<em>{to_work[k]}</em>"
                        elif k == length - 1 and length % 2 == 0:
                            to_work[k] = f"_{to_work[k]}"
                    self.private_what = "".join(to_work)
            if "*" in self.private_what:
                to_work = self.private_what.split("*")
                length = len(to_work)
                if length > 2:
                    for k in range(length):
                        if k % 2 == 1 and not k == length - 1:
                            to_work[k] = f"<b>{to_work[k]}</b>"
                        elif k == length - 1 and length % 2 == 0:
                            to_work[k] = f"*{to_work[k]}"
                    self.private_what = "".join(to_work)

            the_text = f"> <b>{self.private_who}</b>: {self.private_what} -- {date}"
            message = QLabel(the_text)
            try:
                if self.users[self.private_who]:  # This will be always true if set
                    message.setStyleSheet(f"background: black; color: {self.users[self.private_who]};")
            except:
                self.users[self.private_who] = choice(self.color_list)
                message.setStyleSheet(f"background: black; color: {self.users[self.private_who]};")
           # Displaying of the message
            try:
                playsound("./config/notification.mp3", False)
            except:
                pass
            self.private_messages_layout.addWidget(message)
            self.private_scroll.verticalScrollBar().setValue(2000 * self.private_label_amount)
        elif not program_allowed:
            QMessageBox.information(self, "Log in", "Finalize logging in first", QMessageBox.StandardButton.Ok)

    def group_received(self):
        """
        Puts the received group messages on the screen.
        Triggered by an invisible button clicked by the receiver thread.
        :return: None
        """
        if program_allowed and self.group_who not in mute_list:
            self.group_label_amount += 1
            date = asctime()
            date = date.split(" ")
            date = " ".join(date[1:-1])

            for k, v in self.meme_list.items():
                if os.path.exists(v):
                    self.group_what = self.group_what.replace(k, f"<img src='{v}'>")

            if "_" in self.group_what:
                to_work = self.group_what.split("_")
                length = len(to_work)
                if length > 2:
                    for k in range(length):
                        if k % 2 == 1 and not k == length - 1:
                            to_work[k] = f"<em>{to_work[k]}</em>"
                        elif k == length - 1 and length % 2 == 0:
                            to_work[k] = f"_{to_work[k]}"
                    self.group_what = "".join(to_work)
            if "*" in self.group_what:
                to_work = self.group_what.split("*")
                length = len(to_work)
                if length > 2:
                    for k in range(length):
                        if k % 2 == 1 and not k == length - 1:
                            to_work[k] = f"<b>{to_work[k]}</b>"
                        elif k == length - 1 and length % 2 == 0:
                            to_work[k] = f"*{to_work[k]}"
                    self.group_what = "".join(to_work)

            the_text = f"group> {self.group_who}: {self.group_what} -- {date}"
            message = QLabel(the_text)
            try:
                if self.users[self.private_who]:  # This will be always true if set
                    message.setStyleSheet(f"background: black; color: {self.users[self.private_who]};")
            except:
                self.users[self.private_who] = choice(self.color_list)
                message.setStyleSheet(f"background: black; color: {self.users[self.private_who]};")
            try:
                playsound("./config/notification.mp3", False)
            except:
                pass
            self.group_messages_layout.addWidget(message)
            self.group_scroll.verticalScrollBar().setValue(2000 * self.group_label_amount)
        elif not program_allowed:
            QMessageBox.information(self, "Log in", "Finalize logging in first", QMessageBox.StandardButton.Ok)

    def mute(self):
        """
        Same as :mute:
        :return: None
        """
        if program_allowed:
            for k in self.function_list:
                k = False
            self.mute_function = True
            self.private_send.setText("Mute")
            self.group_send.setText("Mute")
            QMessageBox.information(self, "Mute", "Type the usernames to mute below", QMessageBox.StandardButton.Ok)
        else:
            QMessageBox.information(self, "Log in", "Finalize logging in first", QMessageBox.StandardButton.Ok)

    def unmute(self):
        """
        Same as :unmute:
        :return: None
        """
        if program_allowed:
            for k in self.function_list:
                k = False
            self.unmute_function = True
            self.private_send.setText("Unmute")
            self.private_send.setStyleSheet("background: lime; color: black; border-radius: 3px; height: 20px; width: 70px;")
            self.group_send.setText("Unmute")
            self.group_send.setStyleSheet("background: lime; color: black; border-radius: 3px; height: 20px; width: 70px;")
            QMessageBox.information(self, "Unmute", "Type the usernames to unmute below", QMessageBox.StandardButton.Ok)
        else:
            QMessageBox.information(self, "Log in", "Finalize logging in first", QMessageBox.StandardButton.Ok)

    def error_received(self):
        """
        Indeed, this is not for error messages. It displays all sorts of
        messages. This is too, connected to an invisible button clicked
        by the receiver thread.
        :return: None
        """
        QMessageBox.information(self, self.error_info, self.error_explanation,
                                QMessageBox.StandardButton.Ok)
        if self.error_info == "End Message":
            self.close()

    def help(self):
        """
        Prints help messages on the chat screen, both private and group.
        :return: None
        """
        # Yeah this one work without the log in.
        help_message = r"""
        --- All commands and their descriptions ---
        quit --> Quits the program.
        online --> Shows top 100 online users.
        new_target --> Changes your target to your input to this command.
        upload --> Uploads the file specified with your input.
        download --> Downloads all files sent to you.
        mute --> Mutes inputted users.
        unmute --> unmutes inputted users.
        """
        message1 = QLabel(help_message)
        message2 = QLabel(help_message)
        message1.setStyleSheet("background: black; color: #EBCF34;")
        message2.setStyleSheet("background: black; color: #ebcf34;")
        self.private_messages_layout.addWidget(message1)
        self.group_messages_layout.addWidget(message2)
        self.private_label_amount += 5  # becaause this is longer
        self.group_label_amount += 5
        self.private_scroll.verticalScrollBar().setValue(2000 * self.private_label_amount)
        self.group_scroll.verticalScrollBar().setValue(2000 * self.group_label_amount)
        #QMessageBox.information(self, "Help", help_message, QMessageBox.StandardButton.Ok)

    def upload(self):
        """
        Manages uploads. Main load is sent through "send" buttons.
        :return: None
        """
        global up_permit, not_permitted
        if self.upload_started or self.download_started or self.download_function or self.upload_function:
            QMessageBox.information(self, "Collision", "FTP action live, wait", QMessageBox.StandardButton.Ok)
        elif program_allowed:
            up_permit = False
            not_permitted = False
            for k in self.function_list:
                k = False
            self.upload_function = True
            self.private_send.setText("Upload")
            self.private_send.setStyleSheet("background: lime; color: black; border-radius: 3px; height: 20px; width: 70px;")
            self.group_send.setText("Upload")
            self.group_send.setStyleSheet("background: lime; color: black; border-radius: 3px; height: 20px; width: 70px;")
            QMessageBox.information(self, "Upload", "Type the filepath below", QMessageBox.StandardButton.Ok)
        else:
            QMessageBox.information(self, "Log in", "Finalize logging in first", QMessageBox.StandardButton.Ok)

    def download(self):
        global down
        """
        Manages downloads. Main load is received through the
        "receiver" thread.
        :return: None
        """
        if self.upload_started or self.download_started:
            QMessageBox.information(self, "Collision", "FTP action live, wait", QMessageBox.StandardButton.Ok)
        elif program_allowed:
            for k in self.function_list:
                k = False
            self.download_function = True
            self.socket.write(bytes(f"CMD <get> {token} \r\n", "utf-8"))
            while not down:
                sleep(0.01)
        else:
            QMessageBox.information(self, "Log in", "Finalize logging in first", QMessageBox.StandardButton.Ok)

        self.download_function = False
        self.download_started = False
        down = False



def receiver(auth, main, sock: ssl.SSLSocket):
    """
    Main receiver thread. socket listening is done here.
    :param auth: authorization widget
    :param main: main widget
    :param sock: connection socket
    :return: None
    """
    global token, program_allowed, up_permit, not_permitted, down
    main.the_other_thread = threading.get_ident()
    try:
        while True:
            sock.settimeout(None)
            mes = sock.read(4096)
            mes = str(mes)[2:-1].split(" ")
            if mes[0] == "ACCEPT":
                main.token = mes[-2]
                token = mes[-2]
                main.target = auth.target.text()
                main.username = auth.username.text()
                main.status.setText(main.target)
                main.status_group.setText(main.target)
                program_allowed = True
                auth.quit_button.click()
            elif mes[0] == "END" and not program_allowed:
                main.error_info = "End Message"
                main.error_explanation = "Incorrect username or password"
                main.error_received_trigger.click()
            elif mes[0] == "END":
                main.error_info = "End Message"
                res = " ".join(mes[1:-1])
                main.error_explanation = res
                main.error_received_trigger.click()
            elif mes[0] == "TRY":
                auth.info.setText(" ".join(mes[1:-1]))
                auth.username.setText("")
                auth.password.setText("")
            elif mes[0] == "RELAY":
                main.private_who = mes[2]
                main.private_what = " ".join(mes[3:-1])
                main.private_received_trigger.click()
            elif mes[0] == "RELAYG":
                main.group_who = mes[1]
                main.group_what = " ".join(mes[2:-1])
                main.group_received_trigger.click()
            elif mes[0] == "CNT":
                res = " ".join(mes[1:-1])
                main.error_info = "Server message"
                main.error_explanation = res
                main.error_received_trigger.click()
            elif mes[0] == "CMD":
                res = " ".join(mes[1:-1])
                if res == "<file send complete>":
                    down = True
                    main.download_started = False
                main.error_info = "Command response"
                main.error_explanation = res
                main.error_received_trigger.click()
            elif mes[0] == "PROCEED":
                up_permit = True
            elif mes[0] == "STOP":
                not_permitted = True
                main.error_info = "Stop command"
                main.error_explanation = " ".join(mes[1:-1])
                main.error_received_trigger.click()
            elif mes[0] == "BEGIN":
                # i just copied it from the terminal client
                amount = int(mes[1])
                #down = True
                main.download_started = True
                for k in range(amount):
                    new_file = sock.read(4096)
                    new_file = str(new_file)[2:-1].split(" ")
                    name = new_file[1]
                    with open(name, "xb") as save:
                        while True:
                            data = sock.read(4096)
                            control_data = str(data)[2:-1].split(" ")
                            if len(control_data) >= 4:
                                if control_data[-2] == "ENDF" and control_data[-3] == "ENDF" and control_data[-4] == "ENDF":
                                    if len(control_data) > 4:
                                        last_data = bytes(" ".join(control_data[:-4]))
                                        save.write(last_data)
                                    break
                            save.write(data)
                main.download_started = False
                down = True
    except ConnectionResetError:
        pass
    except socket.timeout:
        pass
    except OSError:
        # It is not handled in the terminal version either
        pass
    except ValueError:
        main.error_info = "Server side problem"
        main.error_explanation = "Server closed."
        main.error_received_trigger.click()


if __name__ == "__main__":
    app = QApplication(argv)
    try:
        if os.name == "posix":
            if not os.path.isdir("./config"): raise Exception("Config dir not found")
            if not os.path.exists("./config/configurations.xml"): raise Exception("configurations.xml not found")
            tree = ET.parse("./config/configurations.xml")
            root = tree.getroot()
            ip = root[0][0].text
            address = (ip, int(root[0][1].text))
            timeout = int(root[0][2].text)
            context.load_cert_chain(root[1][0].text, root[1][0].text)
            username = root[2][0].text
            password = root[2][1].text
            target = root[2][2].text
        else:
            if not os.path.isdir(".\config"): raise Exception("Config dir not found")
            if not os.path.exists(".\config\configurations.xml"): raise Exception("configurations.xml not found")
            tree = ET.parse(".\config\configurations.xml")
            root = tree.getroot()
            ip = root[0][0].text
            address = (ip, int(root[0][1].text))
            timeout = int(root[0][2].text)
            context.load_cert_chain(root[1][0].text, root[1][0].text)
            username = root[2][0].text
            password = root[2][1].text
            target = root[2][2].text
        with socket.create_connection(address, timeout=timeout) as out:
            #217.131.197.5
            with context.wrap_socket(out, server_hostname=ip) as s:
                res = QMessageBox.question(None, "Sign up", "Do you want to sign up?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

                window = Widget(s)
                window.show()
                if res == QMessageBox.StandardButton.Yes:
                    authorization_widget = Entry(s, True)
                    authorization_widget.show()
                else:
                    authorization_widget = Entry(s, False)
                    authorization_widget.show()
                if username != "" and username != "*" and password != "" and password != "*" and target != "" and target != "*":
                    authorization_widget.username.setText(username)
                    authorization_widget.password.setText(password)
                    authorization_widget.target.setText(target)
                    authorization_widget.send.click()
                threading.Thread(target=receiver, args=[authorization_widget, window, s]).start()
                # We create invisible buttons that are connected to handler functions to manage threading

                app.exec()
    except ConnectionRefusedError:
        QMessageBox.information(None, "Connection Refused", "Server offline", QMessageBox.StandardButton.Ok)
        app.exec()
    except socket.timeout:
        QMessageBox.information(None, "Timeout", "Connection timed out, check your internet connection", QMessageBox.StandardButton.Ok)
        app.exec()
    except ssl.SSLError:
        QMessageBox.information(None, "TLS", "TLS connection error", QMessageBox.StandardButton.Ok)
        app.exec()
    except Exception as e:
        QMessageBox.information(None, "Unexpected error", f"Error: {e}", QMessageBox.StandardButton.Ok)
        app.exec()
    finally:
        try:
            if os.name == "posix":
                pthread_kill(window.the_other_thread, SIGKILL)
        except:
            pass

