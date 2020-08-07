from loft.activity import Activity
from loft import activity
from abc import ABCMeta, abstractmethod
from loft.behavior_tree import *

class Test:
    @action
    def get_hp(blackboard):
        print(blackboard.get('hp', '-'))

    @action
    def is_low_hp(blackboard):
        return blackboard.get('hp', 1.) < 0.5

    @action
    def fill_hp(blackboard):
        blackboard['hp'] = 1.0

    def __init__(self):
        hp = Selector('CheckHP')
        hp += self.get_hp
        hp += self.is_low_hp
        hp += self.fill_hp
        self.hp = hp

class BehaviorActivity(Activity, metaclass=ABCMeta):
    def __pre_create__(self):
        self._blackboard = {}
        self._root = Sequencer()
        self.hp = Test().hp

    def __idle__(self):
        print(f"Episode: {self.episode}, Step: {self.step}")
        print(f'Behavior Tree: {self.hp.doAction(self._blackboard)}')

    def __post_destroy__(self):
        pass

    @property
    def blackboard(self):
        return getattr(self, '_blackboard', None)

@activity.service
class BehaviorActivityImpl(BehaviorActivity):
    pass

if __name__ == '__main__':
    app = BehaviorActivityImpl()
    app.run(interval=1., episode=10, step=2)