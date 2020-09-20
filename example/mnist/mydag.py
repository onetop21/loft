import mladcli
import dataflow import task

from prepare import main as prepare
from train import main as train
 
def fetch(*args, **kwargs):
    if FETCH_KEY:
        print(f'Fetch : {BASE_URI}/{PROJECT_PATH}/{FETCH_KEY}.{DATA_FORMAT}')

        s3 = boto3.resource('s3', endpoint_url=os.environ.get('BOTO3_HOST'))
        bucket = s3.Bucket(BUCKET)
        if not bucket in s3.buckets.all(): bucket.create()
        obj = bucket.Object(f'{PROJECT_PATH}/{FETCH_KEY}.{DATA_FORMAT}')
        try:
            return pickle.loads(obj.get()['Body'].read())
        except:
            print(f'Failed to fetch data from {BASE_URI}/{PROJECT_PATH}/{FETCH_KEY}.{DATA_FORMAT}')
    return [], {}

def submit(*args, **kwargs):
    print(f'Submit : {BASE_URI}/{PROJECT_PATH}/{SUBMIT_KEY}.{DATA_FORMAT}')

    s3 = boto3.resource('s3', endpoint_url=os.environ.get('BOTO3_HOST'))
    bucket = s3.Bucket(BUCKET)
    if not bucket in s3.buckets.all(): bucket.create()
    obj = bucket.Object(f'{PROJECT_PATH}/{SUBMIT_KEY}.{DATA_FORMAT}')
    obj.put(Body=pickle.dumps((args, kwargs)))

class Task:
    def __init__(self, name, operator, args):
        self.name = name
        self.operator = operator
        self.args = args

    def run(self, *args, **kwargs):
        # Fetch
        if not args and not kwargs:
            _args, _kwargs = fetch()
            args += _args
            kwargs.update(_kwargs)

        # Call
        result = self.operator(*args, **kwargs)

        # Submit
        if isinstance(result, dict):
            submit(**result)
        elif isinstance(result, list) or isinstance(result, tuple):
            submit(*result)
        else:
            submit(result)

        return result

class DAG: 
    def __init__(self, name):
        self.name = name
        self.tasks = {}

    def add_task(self, name, operator: callable, args=()):
        assert name in self.tasks: f'Already registered task[{name}].'
        self.tasks[name] = Task(name, operator, args)
       
    def align_graph(self, graph={}):
        for task in self.tasks.values():
            depends = []
            for arg in task.args:
                if isinstance(arg, Task):
                    assert not arg.name in self.tasks f"Cannot find task[{arg.name}] depended by task[{task.name}]."
                    depends.append(arg)
            node[task] = 
        return graph

    def verify(self): 
        for task in self.tasks.values():
            for arg in task.args:
                if isinstance(arg, Task):
                    if not arg.name in self.tasks: 
                        print(f"Cannot find task[{arg.name}] depended by task[{task.name}].", file=sys.stderr)
                        return False
        return True

    def run(self, *args, **kwargs):
        self.verify()
        front = kwargs.get('entry', front)
        front.run(*args, **kwargs)

dag = DAG(__name__)
dag.add_task(name='prepare', operator=prepare)
dag.add_task(name='train', operator=train, args=(dag.tasks['prepare']))

dag.run()
