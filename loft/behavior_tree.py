import sys
import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor

from itertools import count
from abc import ABCMeta, abstractmethod

loglevel = os.environ.get('loglevel', logging.ERROR)
logging.basicConfig(level=int(loglevel), datefmt='%Y-%M-%d %H:%M:%S', format='[%(levelname)s] %(asctime)s.%(msecs)03d (%(name)s) - %(message)s')
logger = logging.getLogger(__name__)

class Node:
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def doAction(self, blackboard):
        pass

    @property
    def name(self):
        return getattr(self, '_name', self.__class__.__name__)

    @name.setter
    def name(self, name: str):
        self._name = name

# DoActionLogger
def do_action_logger(func):
    def do_action_wrapper(self, blackboard):
        blackboard['_callstack'] = blackboard.get('_callstack', [])
        _callstack = blackboard['_callstack']
        _callstack.append(f'{self.name}({self.__class__.__name__})')
        resp = func(self, blackboard)     
        logger.debug(f'Call Stack: {"::".join(_callstack)} = {resp}')
        _callstack.pop(-1)
        return resp
    return do_action_wrapper

# Leaf
def action(func):
    class Action(Node):
        def __init__(self, name=None, func=None):
            super().__init__(name)
            if callable(func):
                self._func = func
            else:
                raise ValueError('Invalid func parameter.')

        @do_action_logger 
        def doAction(self, blackboard):
            return self._func(blackboard)

    # decorator
    return Action(func.__name__, func)

# Composite
class Composite(Node):
    def __init__(self, name=None):
        super().__init__(name)
        self._nodes = []

    def __iadd__(self, node: Node):
        return self.add(node)

    def add(self, node: Node):
        self._nodes.append(node)
        return self

class Sequencer(Composite):
    @do_action_logger 
    def doAction(self, blackboard):
        for node in self._nodes:
            if node.doAction(blackboard) == False: return False
        return True

class Selector(Composite):
    @do_action_logger 
    def doAction(self, blackboard):
        for node in self._nodes:
            if node.doAction(blackboard) == True: return True
        return False

class Parallel(Composite):
    def __init__(self, name=None, mode='&'):
        super().__init__(name)
        if mode == '&':
            self._result_processor = lambda x: not False in x
        elif mode == '|':
            self._result_processor = lambda x: True in x
        else:
            raise ValueError('Invalid mode parameter.')

    @do_action_logger 
    def doAction(self, blackboard):
        with ThreadPoolExecutor() as executor:
            futures = []
            for node in self._node:
                futures.append(executor.submit(node.doAction, blackboard))
            return self._result_processor([future.result() for future in futures])

# Decorator
class Decorator(Node):
    def __init__(self, name=None):
        super().__init__(name)
        self._node = None
    
    def bind(self, node: Node):
        self._node = node

class Inverter(Decorator):
    @do_action_logger 
    def doAction(self, blackboard):
        if self._node:
            return not self._node.doAction(blackboard)
        else:
            raise RuntimeError('Not binded node.')

class Succeeder(Decorator):
    @do_action_logger 
    def doAction(self, blackboard):
        if self._node:
            return self._node.doAction(blackboard) or True
        else:
            raise RuntimeError('Not binded node.')

class Repeater(Decorator):
    def __init__(self, name=None, interval=1., max_iter=0):
        super().__init__(name)
        self._interval = interval
        self._iter = max_iter

    @do_action_logger 
    def doAction(self, blackboard):
        if self._node:
            for _ in range(self._iter) if self._iter else count(0):
                begin_tick = time.time()
                if self._node.doAction(blackboard): return True
                time.sleep(max(0, self._interval - (time.time() - begin_tick)))
            return False
        else:
            raise RuntimeError('Not binded node.')
        