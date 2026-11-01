"""Estimate the parameters and weight memory of a token embedding and an untied lm_head."""

import argparse

from common import add_common_arguments, positive_int, print_report


def add_arguments(parser):
    parser.add_argument("--vocab", type=positive_int, required=True, help="vocabulary size")
    parser.add_argument(
        "--lm-head",
        action="store_true",
        help="also count an lm_head that does not share weights with the embedding",
    )


def estimate(args):
    tensors = [("embed_tokens.weight", (args.vocab, args.hidden), 1)]
    if args.lm_head:
        tensors.append(("lm_head.weight", (args.vocab, args.hidden), 1))
    return tensors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser)
    add_arguments(parser)
    args = parser.parse_args()
    print_report("Embedding weights", args, estimate(args))


if __name__ == "__main__":
    main()
