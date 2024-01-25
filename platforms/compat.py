import yaml

def yaml_load(f):
    if hasattr(yaml, "FullLoader"):
        return yaml.load(f, Loader=yaml.FullLoader)
    else:
        return yaml.load(f)
