import sys

from frontend.media import image_utils as _image_utils

sys.modules[__name__] = _image_utils
sys.modules["frontend"].image_utils = _image_utils
