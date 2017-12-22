import sys
import os
sys.path.append(os.path.join(os.getcwd(), '/home/estasney/mysite/my_config'))
sys.path.append('/home/estasney/mysite/my_config')
try:
    from home.estasney.mysite.my_config import local_config
    Config = local_config.Config()
except ImportError:
    import web_config
    Config = web_config.Config()

