def get_info(module):
    name = module.__name__[module.__name__.rfind('.'):]
    group = module.__name__[:module.__name__.rfind('.')]

    return {
        'build': {
            'version': module.__version__,
            'artifact': name,
            'group': group
        }
    }