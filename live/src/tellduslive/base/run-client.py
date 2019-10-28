#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import signal
from Client import *

if __name__ == "__main__":
	c = Client()
	#signal.signal(signal.SIGINT, c.shutdown)
	#c.start()
