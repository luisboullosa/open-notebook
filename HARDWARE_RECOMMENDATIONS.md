# Hardware-Specific Model Recommendations

## Windows Desktop (RTX 4060 16GB VRAM + 64GB RAM)

### Recommended Models:
- **qwen2.5:7b** (4.7GB) - Primary chat model
  - Best balance of quality and speed for your hardware
  - 7B parameters fit well in 16GB VRAM
  - Excellent reasoning and instruction following
  
- **qwen2.5:14b** (9.0GB) - Alternative for higher quality
  - Use if you need better reasoning on complex tasks
  - Still fits comfortably in 16GB VRAM
  - Slower but more capable

- **mxbai-embed-large** (669MB) - Embedding model
  - Required for semantic search
  - Already included in auto-setup

### Why these models:
- Your RTX 4060 with 16GB VRAM can easily handle 7B-14B parameter models
- 64GB RAM provides excellent overhead for context and multiple models
- 7B is the sweet spot for daily use (fast + high quality)
- 14B for when you need maximum reasoning capability

---

## Orange Pi 5 Plus (16GB RAM, ARM CPU, no GPU)

### Recommended Models:
- **qwen2.5:3b** (1.9GB) - Primary chat model
  - Optimized for CPU inference
  - Fast enough for responsive chat on ARM
  - Good quality for everyday tasks
  
- **qwen2.5:1.5b** (934MB) - Ultra-fast alternative
  - Use if 3B is too slow
  - Very responsive even on low-power hardware
  - Lower quality but acceptable for simple tasks

- **mxbai-embed-large** (669MB) - Embedding model
  - Required for semantic search
  - Already included in auto-setup

### Why these models:
- Orange Pi has no GPU, relies on CPU inference
- Smaller models (1.5B-3B) run much faster on CPU
- 3B provides good quality without being too slow
- Avoid 7B+ models on CPU - they'll be painfully slow

---

## Summary

| Hardware | Chat Model | Size | Use Case |
|----------|-----------|------|----------|
| **Windows Desktop** | qwen2.5:7b | 4.7GB | Daily use, best balance |
| Windows Desktop | qwen2.5:14b | 9.0GB | Complex reasoning tasks |
| **Orange Pi** | qwen2.5:3b | 1.9GB | Daily use, CPU optimized |
| Orange Pi | qwen2.5:1.5b | 934MB | Ultra-fast, simple tasks |
| Both | mxbai-embed-large | 669MB | Semantic search (required) |

---

## Notes:
- Windows can easily run 7B-14B models with excellent performance
- Orange Pi should stick to 3B or smaller for good response times
- You can run different models on each device using device-specific docker-compose files
- The 7B model will be 3-5x better quality than 3B
- Both devices already have mxbai-embed-large (auto-pulled)
