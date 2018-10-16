#! /usr/bin/env python3
import sys, os, socket, params, time
from threading import Thread
from framedSock import FramedStreamSock

switchesVarDefaults = (
    (('-l', '--listenPort') ,'listenPort', 50008),
    (('-d', '--debug'), "debug", False), # boolean (set if present)
    (('-?', '--usage'), "usage", False), # boolean (set if present)
    )

progname = "echoserver"
paramMap = params.parseParams(switchesVarDefaults)

debug, listenPort = paramMap['debug'], paramMap['listenPort']

if paramMap['usage']:
    params.usage()

lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # listener socket
bindAddr = ("127.0.0.1", listenPort)
lsock.bind(bindAddr)
lsock.listen(5)
print("listening on:", bindAddr)

class ServerThread(Thread):
    requestCount = 0            # one instance / class
    def __init__(self, sock, debug):
        Thread.__init__(self, daemon=True)
        self.fsock, self.debug = FramedStreamSock(sock, debug), debug
        self.start()
    def run(self):
        while True:
            payload = self.fsock.receivemsg()
            if not payload:
                sys.exit(0)
            return_message = payload
            split_payload = payload.decode().split(' ')
            if split_payload[0] == 'put':
                write_file = True
                if os.path.isfile(split_payload[1]):
                    self.fsock.sendmsg(b'overwrite')
                    choice = self.fsock.receivemsg()
                    if not choice:
                        sys.exit(0)
                    if choice != b'y':
                        write_file = False
                else:
                    self.fsock.sendmsg(b'')
                if write_file:
                    file_name = self.fsock.receivemsg()
                    file_contents = self.fsock.receivemsg()
                    if file_name:
                        if os.path.isfile(file_name.decode()): #rename_file
                            file_name = file_name.decode().split('.')
                            file_name[-2] = file_name[-2] + '_copy'
                            file_name = '.'.join(file_name)
                        f = open(str(file_name), 'w')
                        f.write(str(file_contents.decode()))
                        f.close()
                        return_message = b'Transfer Successful!'
                    else:
                        return_message = b'Transfer Cancelled!'
                else:
                    return_message = b'Transfer Cancelled!'
            self.fsock.sendmsg(return_message)


            # msg = self.fsock.receivemsg()
            # if not msg:
            #     if self.debug: print(self.fsock, "server thread done")
            #     return
            # requestNum = ServerThread.requestCount
            # time.sleep(0.001)
            # ServerThread.requestCount = requestNum + 1
            # msg = ("%s! (%d)" % (msg, requestNum)).encode()
            # self.fsock.sendmsg(msg)


while True:
    sock, addr = lsock.accept()
    ServerThread(sock, debug)
