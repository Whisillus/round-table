---
name: llm-model-param-estimation
description: Use when computing the parameter count or weight memory of a transformer LLM component or layer — token embedding and lm_head, RMSNorm or LayerNorm, MHA/GQA/MQA attention, dense or MoE feed-forward, or a whole transformer block — from its dimensions and weight dtype.
metadata:
  workflow: llm-param-estimation
---

# LLM Model Param Estimation

Use this skill to compute how many parameters a transformer component or block has and how much memory its weights take.
Follow the active agent's permissions and the user's authorized scope; loading this skill does not authorize file changes.

## Scope

- Counts weights only: no gradients, optimizer states, activations, or KV cache.
- Assumes no parallelism: every number is for one full copy of the component.
- Supports MHA, GQA, and MQA attention, and dense or MoE feed-forward layers. MLA, linear attention, and state-space layers are not supported; report that instead of approximating them with another type.
- Quantized dtypes count element bits only; scales, zero points, and other quantization metadata are not included.

## Scripts

The scripts are in `scripts/` under this skill's base directory. Run them with `python3 -B` so Python writes no bytecode cache into the skill directory; they use only the standard library and run on Python 3.9 or later. Every script accepts `--hidden` and `--dtype` (`fp32`, `bf16`, `fp16`, `fp8`, `int8`, `int4`, `fp4`; default `bf16`), and `--help` lists the rest.

| Script | Computes | Arguments |
| --- | --- | --- |
| `estimate_embedding.py` | `embed_tokens`, and with `--lm-head` an lm_head that does not share weights with it | `--vocab`, `--lm-head` |
| `estimate_norm.py` | RMSNorm weight, or LayerNorm weight and bias | `--norm-type rmsnorm\|layernorm` |
| `estimate_attention.py` | q, k, v, o projections, optional biases and query/key norms | `--num-head-q`, `--num-head-kv`, `--headdim`, `--attn-bias none\|qkv\|all`, `--qk-norm none\|per-head\|full` |
| `estimate_ffn.py` | dense FFN, or MoE router, routed experts, and shared experts | `--ffn-type dense\|moe`, `--ffn-style gated\|plain`, `--ffn-bias`; dense: `--intermediate`; MoE: `--experts`, `--top-k`, `--moe-intermediate`, `--shared-experts`, `--shared-intermediate`, `--shared-expert-gate`, `--router-bias` |
| `estimate_transformer_block.py` | one block: norm, attention, norm, FFN | the norm, attention, and FFN arguments together |

Argument meanings:

- `--num-head-kv` equals `--num-head-q` for MHA and is 1 for MQA; `--num-head-q` must be divisible by it.
- `--headdim` is given explicitly because some models do not use `hidden / num-head-q`.
- `--attn-bias qkv` adds biases to q, k, and v; `all` also to o.
- `--qk-norm per-head` is one weight of size `headdim` each for query and key, shared by all heads; `full` normalizes the whole query and key projections.
- `--ffn-style gated` is a SwiGLU or GeGLU FFN with gate, up, and down projections; `plain` is a GELU or ReLU FFN with up and down projections. The activation function has no parameters.
- `--shared-intermediate` defaults to `--moe-intermediate`. `--shared-expert-gate` adds a `[1, hidden]` gate on the shared expert output. `--router-bias` adds one value per expert, such as a score-correction bias.

Example, one Llama-3-8B block:

```bash
python3 -B scripts/estimate_transformer_block.py --hidden 4096 --norm-type rmsnorm --num-head-q 32 --num-head-kv 8 --headdim 128 --ffn-type dense --ffn-style gated --intermediate 14336
```

Each script prints its inputs, one row per tensor with shape and parameter count, the total, and the weight memory in bytes, GiB, and GB. MoE results also print the parameters active per token: router, `--top-k` routed experts, and shared experts. Invalid or contradictory arguments stop the script with an error naming the argument.

## Workflow

1. Get every dimension from the user or from a source they point to. Ask for a missing dimension instead of assuming a typical value.
2. Run the script for the component asked about, or `estimate_transformer_block.py` for a whole layer.
3. For a layer that differs from `estimate_transformer_block.py`'s norm, attention, norm, FFN order, such as a model with four norms per block, combine the component scripts and add their totals.
4. For a whole model, add the block totals over the layers, accounting for layers that differ (for example dense layers before MoE layers), plus the embedding, the lm_head if not tied, and the final norm. Count components the scripts do not model, such as learned position embeddings, separately and say so.

## Reporting

- Show the command or the dimensions used, so the result can be checked.
- State the dtype and that the figures are weights only, without parallelism.
- For MoE, give both total and active parameters.
- Name every component that was added by hand or left out.
