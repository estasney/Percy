import sys
import os
sys.path.append(os.path.join(os.getcwd(), '/home/estasney/mysite/modules'))
sys.path.append(os.path.join(os.getcwd(), '/home/estasney/mysite/my_config'))

sys.path.append('/home/estasney/mysite/my_config')
sys.path.append('/home/estasney/mysite/modules')

try:
    from home.estasney.mysite.modules import diversity_tools, neural_tools, text_tools, upload_tools, Utils
except ImportError:
    import diversity_tools, neural_tools, text_tools, upload_tools, Utils


