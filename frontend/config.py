import sys

from frontend.core import config as _config

sys.modules[__name__] = _config
sys.modules["frontend"].config = _config
