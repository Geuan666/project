#!/usr/bin/env python3
import os
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from toolcall_circuit.semantic_schema_stagewise import main


if __name__ == "__main__":
    main()
