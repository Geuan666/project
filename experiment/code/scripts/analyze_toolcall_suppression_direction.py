#!/usr/bin/env python3
from __future__ import annotations

import os
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from toolcall_circuit.suppression_direction_analysis import main


if __name__ == "__main__":
    main()
