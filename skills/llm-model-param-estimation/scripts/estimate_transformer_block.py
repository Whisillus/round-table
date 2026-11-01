"""Estimate the parameters and weight memory of one transformer block.

The block is a pre-attention norm, attention, a pre-FFN norm, and an FFN; it
takes the arguments of estimate_norm.py, estimate_attention.py, and
estimate_ffn.py.
"""

import argparse

import estimate_attention
import estimate_ffn
import estimate_norm
from common import add_common_arguments, print_report, total_params, with_prefix


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common_arguments(parser)
    estimate_norm.add_arguments(parser)
    estimate_attention.add_arguments(parser)
    estimate_ffn.add_arguments(parser)
    args = parser.parse_args()
    estimate_attention.validate(parser, args)
    estimate_ffn.validate(parser, args)

    attention = with_prefix("self_attn.", estimate_attention.estimate(args))
    ffn_tensors, ffn_active = estimate_ffn.estimate(args)
    ffn = with_prefix("mlp.", ffn_tensors)
    input_norm = estimate_norm.estimate(args, "input_layernorm")
    post_attention_norm = estimate_norm.estimate(args, "post_attention_layernorm")
    tensors = input_norm + attention + post_attention_norm + ffn

    active = None
    if args.ffn_type == "moe":
        active = total_params(input_norm + attention + post_attention_norm) + ffn_active
    print_report("Transformer block weights", args, tensors, active)


if __name__ == "__main__":
    main()
