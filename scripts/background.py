#!/usr/bin/python

import os
import sys
import time

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from backpacked import backgroundtasktypes

backgroundtasktypes.ProcessTweetsRealtimeManager().run()
