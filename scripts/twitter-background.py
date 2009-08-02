#!/usr/bin/python

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from travelist import backgroundtasktypes

backgroundtasktypes.ProcessTwitterRealtimeManager().run()
