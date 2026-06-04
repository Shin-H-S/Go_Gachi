import sys

from frontend.work import uploads as _uploads

sys.modules[__name__] = _uploads
sys.modules["frontend"].upload_utils = _uploads
