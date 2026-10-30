# LLM cost vs quality

**Run: Haiku (claude-haiku-5-5) for every rung, dev split, N=51 posts** (53 dev labels; 2 skipped because the posts were deleted from HN: 47625506, 48747987). Run on 2026-10-30, 03:46–04:17 America/Toronto. This is not the repo's pinned Opus model. Errors: C had 1 API timeout (47976872), W had 1 invalid-output validation error (47220989); their costs are marked incomplete.

Model: claude-haiku-5-5. Pricing source: https://platform.claude.com/docs/en/about-claude/pricing.

Unweighted labeled-set scores; parentheses contain 95% Wilson intervals. Skills macro-F1 has no Wilson interval. Costs are USD.

## Config B

| Field | Dev (n=51) | Halluc, dev |
| --- | --- | ---: |
| company | 95.9% (86 to 99) | 0.0% |
| salary | 100.0% (65 to 100) | 0.0% |
| location | 63.4% (48 to 76) | 3.9% |
| skills F1 | 0.757 |  |
| remote | 88.2% accuracy |  |
| seniority | 88.2% accuracy |  |
| Cost, USD | 0.019916 | |
| p50 latency, ms | 1931.5 | |
| p95 latency, ms | 4215.3 | |

## Config C

| Field | Dev (n=51) | Halluc, dev |
| --- | --- | ---: |
| company | 95.6% (85 to 99) | 0.0% |
| salary | 100.0% (57 to 100) | 0.0% |
| location | 60.0% (44 to 74) | 3.9% |
| skills F1 | 0.745 |  |
| remote | 84.3% accuracy |  |
| seniority | 74.5% accuracy |  |
| Cost, USD | 0.087706 (incomplete) | |
| p50 latency, ms | 4909.3 | |
| p95 latency, ms | 21669.4 | |

## Config D

| Field | Dev (n=51) | Halluc, dev |
| --- | --- | ---: |
| company | 97.8% (89 to 100) | 0.0% |
| salary | 100.0% (61 to 100) | 0.0% |
| location | 54.0% (38 to 69) | 3.9% |
| skills F1 | 0.777 |  |
| remote | 82.3% accuracy |  |
| seniority | 84.3% accuracy |  |
| Cost, USD | 0.086981 | |
| p50 latency, ms | 4525.4 | |
| p95 latency, ms | 12832.0 | |

## Config E

| Field | Dev (n=51) | Halluc, dev |
| --- | --- | ---: |
| company | 95.2% (84 to 99) | 0.0% |
| salary | 100.0% (57 to 100) | 0.0% |
| location | 74.3% (58 to 86) | 3.9% |
| skills F1 | 0.749 |  |
| remote | 72.5% accuracy |  |
| seniority | 82.3% accuracy |  |
| Cost, USD | 0.127668 | |
| p50 latency, ms | 5991.8 | |
| p95 latency, ms | 13607.4 | |

## Config W

| Field | Dev (n=51) | Halluc, dev |
| --- | --- | ---: |
| company | 95.8% (86 to 99) | 0.0% |
| salary | 100.0% (65 to 100) | 0.0% |
| location | 65.8% (50 to 79) | 3.9% |
| skills F1 | 0.795 |  |
| remote | 86.3% accuracy |  |
| seniority | 86.3% accuracy |  |
| Cost, USD | 0.015070 (incomplete) | |
| p50 latency, ms | 1370.9 | |
| p95 latency, ms | 3209.9 | |

## Config F

| Field | Dev (n=51) | Halluc, dev |
| --- | --- | ---: |
| company | 87.8% (76 to 94) | 0.0% |
| salary | 100.0% (57 to 100) | 0.0% |
| location | 63.0% (49 to 75) | 13.7% |
| skills F1 | 0.726 |  |
| remote | 88.2% accuracy |  |
| seniority | 70.6% accuracy |  |
| Cost, USD | 0.002890 | |
| p50 latency, ms | 1.8 | |
| p95 latency, ms | 1047.3 | |

