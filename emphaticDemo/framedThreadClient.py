#! /usr/bin/env python3

# Echo client program
import socket, sys, re, os
import params
from framedSock import FramedStreamSock
from threading import Thread
import time

switchesVarDefaults = (
    (('-s', '--server'), 'server', "localhost:50008"),
    (('-d', '--debug'), "debug", False), # boolean (set if present)
    (('-?', '--usage'), "usage", False), # boolean (set if present)
    )


progname = "framedClient"
paramMap = params.parseParams(switchesVarDefaults)

server, usage, debug  = paramMap["server"], paramMap["usage"], paramMap["debug"]

if usage:
    params.usage()


try:
    serverHost, serverPort = re.split(":", server)
    serverPort = int(serverPort)
except:
    print("Can't parse server:port from '%s'" % server)
    sys.exit(1)

class ClientThread(Thread):
    def __init__(self, serverHost, serverPort, debug):
        Thread.__init__(self, daemon=False)
        self.serverHost, self.serverPort, self.debug = serverHost, serverPort, debug
        self.start()
    def run(self):
      s = None
      for res in socket.getaddrinfo(serverHost, serverPort, socket.AF_UNSPEC, socket.SOCK_STREAM):
           af, socktype, proto, canonname, sa = res
           try:
               print("creating sock: af=%d, type=%d, proto=%d" % (af, socktype, proto))
               s = socket.socket(af, socktype, proto)
           except socket.error as msg:
               print(" error: %s" % msg)
               s = None
               continue
           try:
               print(" attempting to connect to %s" % repr(sa))
               s.connect(sa)
           except socket.error as msg:
               print(" error: %s" % msg)
               s.close()
               s = None
               continue
           break

      if s is None:
           print('could not open socket')
           sys.exit(1)

      fs = FramedStreamSock(s, debug=debug)

      # while True:
      #message = input('>>>')
      message = 'put something.txt'
      split_message = message.split(' ')
      if split_message[0] == 'put':
          if os.path.isfile(split_message[1]):
              fs.sendmsg(bytes(message, 'utf-8'))
              error = fs.receivemsg()
              write_file = True
              if error == b'overwrite':
                  while(True):
                      overwrite = 'y' #input('A file with the same name already exists in the server, save as a copy? (y/n)\n')
                      if overwrite == 'y':
                          break
                      elif overwrite == 'n':
                          write_file = False
                          break
                  fs.sendmsg(bytes(overwrite, 'utf-8'))
          
              if write_file:
                  f = open(split_message[1], 'r')
                  contents = f.read()
                  f.close()
                  fs.sendmsg(bytes(split_message[1], 'utf-8'))
                  message = contents
          else: #if file does not exist, ask the user for another input
              print('The file ' + split_message[1] + ' does not exist')
              # continue
      b_message = bytes(message, 'utf-8')
      fs.sendmsg(b_message)
      print("received:", fs.receivemsg())

for i in range(10):
    ClientThread(serverHost, serverPort, debug)

