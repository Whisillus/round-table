"""Estimate the parameters and weight memory of an RMSNorm or LayerNorm."""

import argparse

from common import add_common_arguments, print_report


def add_arguments(parser):
    parser.add_argument(
        "--norm-type",
        choices=("rmsnorm", "layernorm"),
        required=True,
        help="rmsnorm has a weight; layernorm has a weight and a bias",
    )


def estimate(args, name="norm"):
    tensors = [(f"{name}.weight", (args.hidden,), 1)]
    if args.norm_type == "layernorm":
        tensors.append((f"{name}.bias", (args.hidden,), 1))
    return tensors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser)
    add_arguments(parser)
    args = parser.parse_args()
    print_report("Norm weights", args, estimate(args))


if __name__ == "__main__":
    main()
