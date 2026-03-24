#!/usr/bin/env python3
from __future__ import annotations

import os
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

import toolcall_circuit.final_head_attention_audit as final_head_attention_audit


def main() -> None:
    # 只保留 suppression_direction_analysis 真正读取的两个 no-tool 头，
    # 用于更快生成模块 4 依赖的 summary CSV。
    final_head_attention_audit.TOOL_HEADS = []
    final_head_attention_audit.NO_TOOL_HEADS = ["L16H4", "L23H6"]
    final_head_attention_audit.ALL_HEADS = list(final_head_attention_audit.NO_TOOL_HEADS)
    final_head_attention_audit.main()


if __name__ == "__main__":
    main()
