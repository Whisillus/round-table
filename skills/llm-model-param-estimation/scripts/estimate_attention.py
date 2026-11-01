"""Estimate the parameters and weight memory of an MHA, GQA, or MQA attention layer.

MHA has --num-head-kv equal to --num-head-q, MQA has --num-head-kv 1, and GQA
lies between.
"""

import argparse

from common import add_common_arguments, positive_int, print_report


def add_arguments(parser):
    parser.add_argument("--num-head-q", type=positive_int, required=True, help="number of query heads")
    parser.add_argument("--num-head-kv", type=positive_int, required=True, help="number of key/value heads")
    parser.add_argument("--headdim", type=positive_int, required=True, help="dimension of one attention head")
    parser.add_argument(
        "--attn-bias",
        choices=("none", "qkv", "all"),
        default="none",
        help="projections with a bias: none, q/k/v only, or q/k/v/o (default: none)",
    )
    parser.add_argument(
        "--qk-norm",
        choices=("none", "per-head", "full"),
        default="none",
        help="query/key norm weight over one head (per-head) or over all heads (full) (default: none)",
    )


def validate(parser, args):
    if args.num_head_q % args.num_head_kv != 0:
        parser.error(
            f"--num-head-q ({args.num_head_q}) must be divisible by --num-head-kv ({args.num_head_kv})"
        )


def estimate(args):
    q_size = args.num_head_q * args.headdim
    kv_size = args.num_head_kv * args.headdim
    tensors = [
        ("q_proj.weight", (q_size, args.hidden), 1),
        ("k_proj.weight", (kv_size, args.hidden), 1),
        ("v_proj.weight", (kv_size, args.hidden), 1),
        ("o_proj.weight", (args.hidden, q_size), 1),
    ]
    if args.attn_bias in ("qkv", "all"):
        tensors += [
            ("q_proj.bias", (q_size,), 1),
            ("k_proj.bias", (kv_size,), 1),
            ("v_proj.bias", (kv_size,), 1),
        ]
    if args.attn_bias == "all":
        tensors.append(("o_proj.bias", (args.hidden,), 1))
    if args.qk_norm == "per-head":
        tensors += [
            ("q_norm.weight", (args.headdim,), 1),
            ("k_norm.weight", (args.headdim,), 1),
        ]
    elif args.qk_norm == "full":
        tensors += [
            ("q_norm.weight", (q_size,), 1),
            ("k_norm.weight", (kv_size,), 1),
        ]
    return tensors


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common_arguments(parser)
    add_arguments(parser)
    args = parser.parse_args()
    validate(parser, args)
    print_report("Attention weights", args, estimate(args))


if __name__ == "__main__":
    main()
