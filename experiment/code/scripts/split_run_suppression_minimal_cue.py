#!/usr/bin/env python3
from __future__ import annotations

import os
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

import toolcall_circuit.minimal_cue_mechanism as minimal_cue_mechanism


def main() -> None:
    # 模块 4 只需要 no-tool family 的 node/edge 证据。
    # 这里保留必要节点扫描，但去掉 tool-family 的 stagewise / edge loops，
    # 以更快生成 suppression 适配所需的 summary 文件。
    minimal_cue_mechanism.TOOL_CHAIN = []
    minimal_cue_mechanism.TOOL_EDGES = []
    minimal_cue_mechanism.main()


if __name__ == "__main__":
    main()
