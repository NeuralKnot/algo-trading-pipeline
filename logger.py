# Logs to message queue
import arrow

class Logger:
    def __init__(self, message_queue):
        self.message_queue = message_queue

    def log(self, source, msg_type, message):
        time = str(arrow.now())

        message = ''.join(ch for ch in message if ch.isalnum() or ch == " ")

        message_final = "[" + time + "] " + "[" + source + "] " + "[" + msg_type + "] " + "[" + message + "]"
        self.message_queue.put(message_final)
