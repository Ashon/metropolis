import importlib


def get_module(module_path):
    module_path, _, child_name = module_path.rpartition('.')

    module = importlib.import_module(module_path)
    child = getattr(module, child_name)

    return module, child
