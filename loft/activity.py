import sys
import os
import time
from threading import Thread
from itertools import count
import signal
from contextlib import contextmanager
import logging
from abc import ABCMeta, abstractmethod

loglevel = os.environ.get('loglevel', logging.ERROR)
logging.basicConfig(level=int(loglevel), datefmt='%Y-%M-%d %H:%M:%S', format='[%(levelname)s] %(asctime)s.%(msecs)03d (%(name)s) - %(message)s')
logger = logging.getLogger(__name__)

@contextmanager
def Timeout(t):
    def alarm_func(t):
        time.sleep(t)
        os.kill(os.getpid(), signal.SIGALRM)
    alarm = Thread(target=alarm_func, args=(t,))
    def raise_timeout_error(signum, frame):
        raise TimeoutError
    signal.signal(signal.SIGALRM, raise_timeout_error)

    alarm.start()
    try:
        yield
    except TimeoutError:
        pass
    finally:
        signal.signal(signal.SIGALRM, signal.SIG_IGN)
    alarm.join()

class Activity(metaclass=ABCMeta):
    def __pre_create__(self): pass
    def __idle__(self): pass
    def __post_destroy__(self): pass

    def onCreate(self): pass
    def onStart(self): pass
    def onStep(self): pass
    def onStop(self): pass
    def onDestroy(self): pass

    @property
    def episode(self):
        return getattr(self, '_episode', 0) 

    @property
    def step(self):
        return getattr(self, '_step', 0) 

    def join(self):
        self.__thread.join()

def service(clazz):
    class ActivityWrapper(clazz):
        def __init__(self, *args, **kwargs):
            if not issubclass(clazz, Activity):
                raise ValueError(f'Invalid class type [{clazz.__class__.__name__}].')
            super().__init__(*args, **kwargs)

        def run(self, interval=1., episode=0, step=0):
            self._episode = 0
            self._step = 0
            if self.__pre_create__() != False:
                if self.onCreate() != False:
                    for self._episode in range(episode) if episode else count(0):
                        if self.onStart() != False:
                            for self._step in range(step) if step else count(0):
                                begin_tick = time.time()
                                if self.onStep() == False: break
                                with Timeout(max(0, interval - (time.time() - begin_tick))):
                                    self.__idle__()
                                time.sleep(max(0, interval - (time.time() - begin_tick)))
                        if self.onStop() == False: break
                self.onDestroy()
            self.__post_destroy__()

        def runAsync(self, interval=1., episode=0, step=0):
            self.__thread = Thread(target=lambda *args: self.run(*args), args=(interval, episode, step), daemon=True)
            self.__thread.start()
            return self.__thread

        def join(self):
            self.__thread.join()

    return ActivityWrapper

