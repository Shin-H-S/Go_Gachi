import sys

from frontend.core import router as _router

sys.modules[__name__] = _router
sys.modules["frontend"].router = _router
