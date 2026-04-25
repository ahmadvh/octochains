## Hardware Notes: Running Parallel Agents Locally

You might assume that running 4 agents simultaneously requires loading the model into your GPU 4 separate times, causing an Out-Of-Memory (OOM) crash. However, **Octochains** running alongside modern inference engines (like Ollama/llama.cpp) is highly optimized for parallel execution.

### How 4 Agents fit into ~3GB of VRAM:

1. **Shared Model Weights:** The heaviest part of an LLM is its weights (the neural network). Because weights are read-only during inference, the engine loads the model (e.g., `llama3.2:3b`) into VRAM exactly **once** (~2.5GB).
2. **Independent KV Caches:** While the "brain" is shared, each agent needs its own "short-term memory" for its specific prompt and context. The engine allocates a tiny Key-Value (KV) Cache for each concurrent thread.
3. **The Math:** `2.5GB (Shared Weights) + (~125MB KV Cache × 4 Agents) ≈ ~3GB Total VRAM.`

### Context Windows are Not Shared
Even though the agents share the model weights, they **do not share context limits**. Every agent gets its own independent context window (e.g., 8,192 tokens). Because Octochains broadcasts highly targeted, distinct goals to each agent, the KV cache footprint remains incredibly small.

### Scaling with Heterogeneous Models
If you assign a *different* model to each agent (e.g., Llama, Phi, Gemma, and Qwen), the engine *will* load all four sets of weights into VRAM. This will utilize more memory (e.g., ~9GB total), but it unlocks true **Cognitive Diversity**, completely eliminating shared blindspots across the expert panel.