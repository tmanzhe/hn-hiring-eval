# web

Next.js 16 on Cloud Run. Built, step 27 and 28.

    npm install
    API_URL=http://127.0.0.1:8000 npm run dev

Every fetch runs on the server, so `API_URL` never reaches the browser and the container can
talk to the API over an internal address. `/api/match` is a proxy and nothing more: the ranking
happens in FastAPI, and this side does not reorder it.

Four routes:

| Route | What |
| --- | --- |
| `/` | paste a resume, get ranked matches and skill gaps |
| `/jobs` | browse and filter the current thread |
| `/trends` | skill demand over time |
| `/evals` | the Pareto table, per-field scores with error bars, slice breakdown, failure taxonomy |

`/evals` is the one that matters. Most projects bury that material in a README; putting it in the
product is what makes the whole argument visible in one scroll.

Chosen over Streamlit deliberately. Streamlit reads as a notebook, not a product.

The charts are hand-written SVG. A charting library is four hundred kilobytes to draw six
polylines, and the shape of this data does not need one.

`/evals` renders whatever `/api/evals` returns, including nothing. Until the sample is labeled
and a run is recorded it says so in plain words rather than showing a placeholder, because a
made-up number on the evals page would be the one figure on the site nobody could check.
