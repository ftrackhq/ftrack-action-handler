import sys
import Queue
import logging
import threading

logger = logging.getLogger(
    __name__
)

class ActionWorker(threading.Thread):
    def __init__(self, queue):
        super(ActionWorker, self).__init__()

        self.queue = queue
        self.running = threading.Event()

        self.start()

    def join(self):
        self.running.set()

    def run_action(self, fn=None, args=None, session=None, callback=None):
        result = fn(
            session, *args
        )

        callback(
            session, result, *args
        )

    def run(self):
        while not self.running.isSet():
            try:
                action = self.queue.get(
                    True, timeout=0.1
                )

                self.run_action(
                    **action
                )

            except Queue.Empty:
                continue

            except Exception:
                sys.excepthook(
                    *sys.exc_info()
                )
