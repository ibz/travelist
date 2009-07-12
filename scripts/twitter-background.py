#!/usr/bin/python

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from backpacked import backgroundtasktypes

backgroundtasktypes.ProcessTwitterRealtimeManager().run()
