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
        threading.Thread.__init__(self)
        ip = (([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")] or [[(s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) + ["no IP found"])[0]
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((ip, self.port))
        self.sock.settimeout(1)
        self.close = False

    def run(self):
        while not self.close:
            self.listen()
            self.flush_send()

    def listBocking(self, id):
        idMsgs = []
        while not idMsgs:
            with self.readlock:
                if id in self.msgs:
                    idMsgs = self.msgs[id]
                    self.msgs[id] = []
                if id == -1:
                    for k, m in self.msgs:
                        if m.qr:
                            idMsgs += [m]
        return idMsgs

    def listen(self):
        if self.close:
            self.sock.close()
            return
        r, _, _ = select.select([self.sock], [], [], 0.00)
        if r:
            data = self.sock.recv(1024)
            msg = message.Message.from_bytes(data)
            id = msg.header.ident
            if id in self.msgs:
                self.msgs[id] += [msg]
            else:
                self.msgs[id] = [msg]

    def flush_send(self):
        while not self.q.empty():
            i = self.q.get()
            print(i[1])
            self.sock.sendto(i[0].to_bytes(), (i[1], self.port))

    def msgThere(self, id):
        idMsgs = []
        with self.readlock:
            if id in self.msgs:
                idMsgs = self.msgs[id]
                self.msgs[id] = []
            if id==-1:
                for k,m in self.msgs:
                    if not m.qr:
                        idMsgs += [m]
        return idMsgs

    def send(self, msg):
        """
        :param msg: tuple of shape (msg, ip, port)
        :return:
        """
        self.q.put(msg)

    def shutdown(self):
        self.sock.shutdown()
        self.close = True
