from threading import Lock
import socket
from dns import message
import queue
import select
import threading


class SocketWrapper(threading.Thread):
    readlock = Lock()
    msgs = {}
    q = queue.Queue(42)

    def __init__(self, port):
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('localhost', self.port))
        self.sock.settimeout(0.1)
        self.close = False

    def run(self):
        while not self.close:
            self.listen()
            self.flush_send()

    def listen(self):
        if self.close:
            self.sock.close()
            return
        r, _, _ = select.select([self.sock], [], [], 0.1)
        if r:
            data, addr = self.sock.recvfrom(1024, )
            msg = message.Message.from_bytes(data)
            id = msg.header.ident
            if id in self.msgs:
                self.msgs[id] += msg
            else:
                self.msgs[id] = [msg]

    def flush_send(self):
        while not self.q.empty():
            i = self.q.get()
            self.sock.sendto(i[0].to_bytes(), (i[1], i[2]))

    def msgThere(self, id):
        idMsgs = []
        with self.readlock:
            if id in self.msgs:
                idMsgs = self.msgs[id]
                self.msgs[id] = []
        return idMsgs

    def send(self, msg):
        """
        :param msg: tuple of shape (msg, ip, port)
        :return:
        """
        self.q.add(msg)

    def shotdown(self):
        self.close = True
