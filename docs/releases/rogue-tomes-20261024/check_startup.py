"""Read-only early check of native boot cleanup before scheduling any outage."""
import importlib.util,json
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=load('base','/opt/nightcap/releases/classic-dungeons-rewards-20261022/rollout.py')
startup=load('startup','/opt/nightcap/releases/aa-level-progression-20261023-v3/rollout.py');startup.sql=base.sql
print(json.dumps({'startup_guards':startup.startup_guards()}))
