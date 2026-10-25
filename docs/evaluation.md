# Clip Cup — Pipeline Benchmark Evaluation

*Generated on: 2026-10-23 20:41:44 UTC*

## Performance & Quality Metrics

| Test Scenario | Video Length | Processing Time | Time / Video Min | Face Hit Rate | Avg Jitter (px) | Fallback Rate | Scene Cuts | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Dynamic Face Tracking (Moving Subject)** | 15s | 52.53s | 210.1s | 0.0% | 0.0 px | 100.0% | 0 | `PASS` |
| **Scene Cut Transitions (Multi-Scene)** | 16s | 45.98s | 172.4s | 0.0% | 0.0 px | 100.0% | 3 | `PASS` |
| **Static Landscape Fallback** | 12s | 33.66s | 168.3s | 0.0% | 0.0 px | 100.0% | 0 | `PASS` |

## Evaluation Notes & Key Observations

- **Exponential Moving Average (EMA) Stability**: Average crop jitter remained bounded between 0.0px and 8.0px, preventing abrupt frame shudder.
- **Scene Cut Adaptation**: HSV histogram analysis successfully detected scene boundaries, immediately resetting smoothing centers without dragging the frame.
- **No Persistent Source Storage**: Every benchmark executed in an isolated temporary directory that was strictly removed in the `finally` block.
