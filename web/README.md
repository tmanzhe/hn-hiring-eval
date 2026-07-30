# web

Next.js on Cloud Run. Not built yet — Phase 4.

Four routes:

| Route | What |
| --- | --- |
| `/` | paste a resume, get ranked matches and skill gaps |
| `/jobs` | browse and filter the current thread |
| `/trends` | skill demand over time |
| `/evals` | the Pareto table, per-field scores with error bars, slice breakdown, failure taxonomy |

`/evals` is the one that matters. Most projects bury that material in a README; putting it in the
product is what makes the whole argument visible in one scroll.

Chosen over Streamlit deliberately — Streamlit reads as a notebook, not a product.
