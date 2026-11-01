"""Shared argument types, dtype sizes, and report output for the estimate_* scripts."""

import argparse
import math

DTYPE_BITS = {
    "fp32": 32,
    "bf16": 16,
    "fp16": 16,
    "fp8": 8,
    "int8": 8,
    "int4": 4,
    "fp4": 4,
}


def positive_int(text):
    value = int(text)
    if value <= 0:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {text}")
    return value


def add_common_arguments(parser):
    parser.add_argument("--hidden", type=positive_int, required=True, help="hidden size")
    parser.add_argument("--dtype", choices=DTYPE_BITS, default="bf16", help="weight dtype (default: bf16)")


def total_params(tensors):
    return sum(count * math.prod(shape) for _, shape, count in tensors)


def print_report(title, args, tensors, active_params=None):
    """Print inputs, one row per tensor, totals, and weight memory.

    A tensor is (name, shape, count); count > 1 stands for identical tensors,
    such as one projection repeated across experts.
    """
    print(title)
    print("Inputs: " + " ".join(f"{key}={value}" for key, value in vars(args).items() if value is not None))
    print()

    rows = []
    for name, shape, count in tensors:
        shape_text = "[" + ", ".join(str(size) for size in shape) + "]"
        if count > 1:
            shape_text = f"{count} x {shape_text}"
        rows.append((name, shape_text, f"{count * math.prod(shape):,}"))
    headers = ("Tensor", "Shape", "Params")
    widths = [max(len(row[column]) for row in rows + [headers]) for column in range(3)]
    for name, shape_text, params in [headers] + rows:
        print(f"{name:<{widths[0]}}  {shape_text:<{widths[1]}}  {params:>{widths[2]}}")
    print()

    total = total_params(tensors)
    print(f"Total params: {total:,}")
    if active_params is not None:
        print(f"Active params per token: {active_params:,}")
    # Round each tensor up to whole bytes: an odd element count in a 4-bit dtype still occupies a whole byte.
    weight_bytes = sum(count * math.ceil(math.prod(shape) * DTYPE_BITS[args.dtype] / 8) for _, shape, count in tensors)
    print(
        f"Weight memory ({args.dtype}): {weight_bytes:,} bytes"
        f" = {weight_bytes / 2**30:.3f} GiB = {weight_bytes / 1e9:.3f} GB"
    )
