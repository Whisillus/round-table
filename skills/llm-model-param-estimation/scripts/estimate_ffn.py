"""Estimate the parameters and weight memory of a dense or MoE feed-forward layer.

A gated FFN (SwiGLU, GeGLU) has gate, up, and down projections; a plain FFN
(GELU, ReLU) has up and down projections. The activation function itself has no
parameters.
"""

import argparse

from common import add_common_arguments, positive_int, print_report, total_params

MOE_ONLY_ARGUMENTS = (
    "experts",
    "top_k",
    "moe_intermediate",
    "shared_experts",
    "shared_intermediate",
    "shared_expert_gate",
    "router_bias",
)


def add_arguments(parser):
    parser.add_argument("--ffn-type", choices=("dense", "moe"), required=True, help="dense FFN or mixture of experts")
    parser.add_argument(
        "--ffn-style",
        choices=("gated", "plain"),
        required=True,
        help="gated: gate/up/down projections; plain: up/down projections",
    )
    parser.add_argument("--ffn-bias", action="store_true", help="FFN projections have a bias")
    parser.add_argument("--intermediate", type=positive_int, help="dense: intermediate size")
    parser.add_argument("--experts", type=positive_int, help="moe: number of routed experts")
    parser.add_argument("--top-k", type=positive_int, help="moe: routed experts active per token")
    parser.add_argument("--moe-intermediate", type=positive_int, help="moe: intermediate size of one routed expert")
    parser.add_argument("--shared-experts", type=positive_int, help="moe: number of shared experts (default: none)")
    parser.add_argument(
        "--shared-intermediate",
        type=positive_int,
        help="moe: intermediate size of one shared expert (default: --moe-intermediate)",
    )
    parser.add_argument(
        "--shared-expert-gate",
        action="store_true",
        help="moe: a [1, hidden] gate scales the shared expert output",
    )
    parser.add_argument("--router-bias", action="store_true", help="moe: the router has one bias per expert")


def validate(parser, args):
    if args.ffn_type == "dense":
        if args.intermediate is None:
            parser.error("--ffn-type dense requires --intermediate")
        passed = [name for name in MOE_ONLY_ARGUMENTS if getattr(args, name) not in (None, False)]
        if passed:
            options = ", ".join("--" + name.replace("_", "-") for name in passed)
            parser.error(f"--ffn-type dense does not accept {options}")
        return

    if args.intermediate is not None:
        parser.error("--ffn-type moe uses --moe-intermediate and --shared-intermediate, not --intermediate")
    for name in ("experts", "top_k", "moe_intermediate"):
        if getattr(args, name) is None:
            parser.error(f"--ffn-type moe requires --{name.replace('_', '-')}")
    if args.top_k > args.experts:
        parser.error(f"--top-k ({args.top_k}) cannot exceed --experts ({args.experts})")
    if not args.shared_experts and (args.shared_intermediate is not None or args.shared_expert_gate):
        parser.error("--shared-intermediate and --shared-expert-gate require --shared-experts")


def projections(prefix, hidden, intermediate, style, bias, count):
    tensors = []
    input_projections = ("gate_proj", "up_proj") if style == "gated" else ("up_proj",)
    for name in input_projections:
        tensors.append((f"{prefix}{name}.weight", (intermediate, hidden), count))
        if bias:
            tensors.append((f"{prefix}{name}.bias", (intermediate,), count))
    tensors.append((f"{prefix}down_proj.weight", (hidden, intermediate), count))
    if bias:
        tensors.append((f"{prefix}down_proj.bias", (hidden,), count))
    return tensors


def estimate(args):
    """Return the tensors and the parameters active for one token."""
    if args.ffn_type == "dense":
        tensors = projections("", args.hidden, args.intermediate, args.ffn_style, args.ffn_bias, 1)
        return tensors, total_params(tensors)

    router = [("router.weight", (args.experts, args.hidden), 1)]
    if args.router_bias:
        router.append(("router.bias", (args.experts,), 1))
    experts_prefix = f"experts.{{0..{args.experts - 1}}}." if args.experts > 1 else "experts.0."
    experts = projections(
        experts_prefix, args.hidden, args.moe_intermediate, args.ffn_style, args.ffn_bias, args.experts
    )
    shared = []
    if args.shared_experts:
        shared_intermediate = args.shared_intermediate or args.moe_intermediate
        shared_prefix = (
            f"shared_experts.{{0..{args.shared_experts - 1}}}." if args.shared_experts > 1 else "shared_experts.0."
        )
        shared = projections(
            shared_prefix, args.hidden, shared_intermediate, args.ffn_style, args.ffn_bias, args.shared_experts
        )
        if args.shared_expert_gate:
            shared.append(("shared_expert_gate.weight", (1, args.hidden), 1))

    one_expert = total_params(experts) // args.experts
    active = total_params(router) + args.top_k * one_expert + total_params(shared)
    return router + experts + shared, active


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common_arguments(parser)
    add_arguments(parser)
    args = parser.parse_args()
    validate(parser, args)
    tensors, active = estimate(args)
    print_report("FFN weights", args, tensors, active if args.ffn_type == "moe" else None)


if __name__ == "__main__":
    main()
