# Class for storing sent & received messages

class MessageLog:
    MAX_TX = 30
    MAX_RX = 100

    def __init__(self):
        self.received = []
        self.sent = []

    #def pop_if_full(self, buffer):
    #    if buffer == 'received':
    #        if len(self.received) > MessageLog.MAX_RX:
    #            self.received = self.received[1:]
    #    else:
    #        if len(self.sent) > MessageLog.MAX_TX:
    #            self.sent = self.sent[1:]

    def log(self, timestamp, message, direction):
        if direction == 'sent':
            self.sent.append((timestamp, message))
            #self.pop_if_full('sent')
        else:
            self.received.append((timestamp, message))
            #self.pop_if_full('received')

    def get_message(self, direction):
        if direction == 'sent':
            if self.sent:
                msg = self.sent[0]
                self.sent = self.sent[1:]
                return msg
        else:
            if self.received:
                msg = self.received[0]
                self.received = self.received[1:]
                return msg
