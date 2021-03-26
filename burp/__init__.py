from __future__ import absolute_import
from .burp import *
from types import ModuleType
import sys

# Install empty Java modules
module = ModuleType("java")
sys.modules["java"] = module
module = ModuleType("java.net")
sys.modules["java.net"] = module
