import asyncore
import socket
import logging
import logging.handlers
import SocketServer
import struct
import pickle
import threading


class LogRecordStreamHandler(SocketServer.StreamRequestHandler):
    """Handler for a streaming logging request.

    This basically logs the record using whatever logging policy is
    configured locally.
    """

    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        according to whatever policy is configured locally.
        """
        while True:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            # added by Andrei
            #self.server.total_clients += 1

            slen = struct.unpack('>L', chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))
            obj = self.unPickle(chunk)
            record = logging.makeLogRecord(obj)
            self.handleLogRecord(record)
        #print(self.server.total_clients)

    def unPickle(self, data):
        return pickle.loads(data)

    def handleLogRecord(self, record):
        # if a name is specified, we use the named logger rather than the one
        # implied by the record.
        #if self.server.logname is not None:
        #    # self.server will be added to this handler object by the server
        #    # that receives the handler at init time.
        #    name = self.server.logname
        #else:
        #    name = record.name
        name = record.name
        logger = logging.getLogger(name)
        # multiple calls to .getLogger(name) will return same object with name
        # "name"; name will be the name of the loggers used in client
        # application to send the logs
        # if self.server.logname exists, there will be only one logger object
        # created

        # N.B. EVERY record gets logged. This is because Logger.handle
        # is normally called AFTER logger-level filtering. If you want
        # to do filtering, do it at the client end to save wasting
        # cycles and network bandwidth!
        logger.handle(record)


class EchoHandler(asyncore.dispatcher_with_send):

    def handle_read(self):
        data = self.recv(8192)
        if data:
            self.send(data)


class EchoServer(asyncore.dispatcher):

    def __init__(self, host='localhost', port=logging.handlers.DEFAULT_TCP_LOGGING_PORT):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print 'Incoming connection from %s' % repr(addr)
            #handler = EchoHandler(sock)
            self.handler = LogRecordStreamHandler(sock, addr, self)

    def handle_read(self):
        self.handler.handle()


if __name__ == '__main__':
    #server = EchoServer('localhost', 8080)
    logging.basicConfig(
        format='%(relativeCreated)5d %(name)-15s %(levelname)-8s %(message)s')
    server = EchoServer()
    #asyncore.loop()
    #server_thread = threading.Thread(target=asyncore.loop)
    # Exit the server thread when the main thread terminates
    #server_thread.daemon = True
    #server_thread.start()
