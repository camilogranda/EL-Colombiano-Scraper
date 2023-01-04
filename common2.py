import yaml

__config2 = None

def config():
    global __config2
    if not __config2:
        with open('config2.yaml', mode='r') as f:
            __config2 = yaml.load(f, Loader=yaml.SafeLoader)
    
    return __config2
