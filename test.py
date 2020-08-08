from loft.activity import Activity
from loft import activity
from abc import ABCMeta, abstractmethod
from loft.behavior_tree import *

class BehaviorActivity(Activity, metaclass=ABCMeta):
    def __pre_create__(self):
        self._blackboard = {}
        self._root = Sequencer()

    def __idle__(self):
        self
        print(f"Episode: {self.episode}, Step: {self.step}")

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