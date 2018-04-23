import socket

from dns.classes import Class
from dns.message import Message, Question, Header
from dns.name import Name
from dns.rtypes import Type
from dns import cache
from dns.zone import Zone
from dns.resource import ResourceRecord

def main():
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

  question = Question(Name("stupid.ourdomain.com"), Type.A, Class.IN)
  header = Header(9001, 0, 1, 0, 0, 0)
  header.qr = 0  # 0 for query
  header.opcode = 0 # standad query
  header.rd = 1 # not recursive
  query = Message(header, [question])

  sock.sendto(query.to_bytes(), (socket.gethostbyname(socket.gethostname()), 53))
  data, addr = sock.recvfrom(512)
  mess = Message.from_bytes(data)
  """
  answer =  ResourceRecord.to_dict(mess.answers[0])
  auth = ResourceRecord.to_dict(mess.authorities[0])
  addi = ResourceRecord.to_dict(mess.additionals[0])
"""
  rrs = []
  rrs += mess.answers + mess.authorities + mess.additionals
  for r in rrs:
    print("R", r.to_dict())
  print(addr)

if __name__ == '__main__':
  main()