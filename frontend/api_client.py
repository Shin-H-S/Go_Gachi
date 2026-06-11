import sys

from frontend.services import api_client as _api_client

sys.modules[__name__] = _api_client
sys.modules["frontend"].api_client = _api_client
