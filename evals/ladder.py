"""Run B, C, D, E and W on the same labels and write a Markdown quality/cost table."""

import argparse
import json
import math
import os
import statistics
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evals.run import load_labels, score_rows
from ingest.corpus import by_id, to_text
from ingest.normalize import normalize


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--split', choices=['dev', 'held-out', 'all'], default='dev')
    ap.add_argument('--limit', type=int, help='first N labeled posts per selected split')
    ap.add_argument('--output', type=Path, default=Path('evals/cost-quality.md'))
    args = ap.parse_args()
    if args.limit is not None and args.limit <= 0:
        ap.error('--limit must be positive')
    if args.output.suffix.lower() != '.md':
        ap.error('--output must end in .md; the JSON details use the same stem with .json')
    detail = args.output.with_suffix('.json')
    if args.output.is_dir() or detail.is_dir():
        ap.error('--output and its .json companion must be file paths, not directories')
    if not os.environ.get('ANTHROPIC_API_KEY', '').strip():
        ap.error('ANTHROPIC_API_KEY is missing. Copy .env.example to .env, fill it in, '
                 'and run with uv run --env-file .env --extra agent evals/ladder.py')
    rates = {}
    for kind in ('INPUT', 'OUTPUT', 'CACHE_READ', 'CACHE_WRITE'):
        name = f'LLM_{kind}_USD_PER_MTOK'
        try:
            value = float(os.environ[name])
            if not math.isfinite(value) or value < 0:
                raise ValueError
        except (KeyError, ValueError):
            ap.error(f'{name} must be a finite nonnegative USD price per million tokens; '
                     'fill in the pricing section of .env.example for STRONG_MODEL')
        rates[kind.lower()] = value
    source = os.environ.get('LLM_PRICE_SOURCE', '').strip()
    model = os.environ.get('STRONG_MODEL', '').strip()
    if not source or not model:
        ap.error('Set STRONG_MODEL and LLM_PRICE_SOURCE in .env to attribute the run and prices')

    from langchain_anthropic import ChatAnthropic
    from langchain_core.callbacks import BaseCallbackHandler

    from agent.extract_agent import extract as agent_extract
    from agent.workflow import extract as workflow_extract

    class Usage(BaseCallbackHandler):
        def __init__(self):
            self.tokens = dict.fromkeys(rates, 0)
            self.missing = False
            self.responses = 0

        def on_llm_end(self, response, **kwargs):
            self.responses += 1
            if not response.generations or not any(response.generations):
                self.missing = True
            for generations in response.generations:
                for generation in generations:
                    usage = getattr(getattr(generation, 'message', None), 'usage_metadata', None)
                    if not isinstance(usage, dict):
                        self.missing = True
                        continue
                    details = usage.get('input_token_details') or {}
                    if not isinstance(details, dict):
                        self.missing = True
                        continue
                    read = details.get('cache_read', 0)
                    write = details.get('cache_creation', 0)
                    input_tokens = usage.get('input_tokens')
                    output_tokens = usage.get('output_tokens')
                    if (any(type(n) is not int or n < 0
                            for n in (input_tokens, output_tokens, read, write))
                            or input_tokens < read + write):
                        self.missing = True
                        continue
                    # LangChain input_tokens includes both cache categories.
                    self.tokens['input'] += input_tokens - read - write
                    self.tokens['output'] += output_tokens
                    self.tokens['cache_read'] += read
                    self.tokens['cache_write'] += write

        def on_llm_error(self, error, **kwargs):
            # A later successful call must not hide unreported usage from a failed call.
            self.missing = True

    splits = ['dev', 'held-out'] if args.split == 'all' else [args.split]
    datasets = {}
    for split in splits:
        labels, label_source = load_labels(split)
        if args.limit:
            labels = labels[:args.limit]
        posts = by_id([label['comment_id'] for label in labels])
        datasets[split] = (labels, posts, label_source)

    rows = []
    for config in ('B', 'C', 'D', 'E', 'W'):
        for split, (labels, posts, label_source) in datasets.items():
            usage = Usage()
            # Disable SDK retries: a retry can hide a billed response whose usage was lost.
            chat = ChatAnthropic(model=model, max_tokens=4096, callbacks=[usage], max_retries=0)
            pairs, latencies, errors = [], [], []
            for label, post in zip(labels, posts, strict=True):
                previous_responses = usage.responses
                started = time.perf_counter()
                text = to_text(post.get('comment_text'))
                if config == 'W':
                    prediction, trace = workflow_extract(text, model=model, chat_model=chat)
                else:
                    result = agent_extract(text, config, model=model, chat_model=chat)
                    prediction, trace = result.extraction, result.trajectory
                latencies.append((time.perf_counter() - started) * 1000)
                if usage.responses == previous_responses:
                    usage.missing = True
                pairs.append((normalize(prediction), label))
                if trace.error:
                    errors.append({'comment_id': label['comment_id'], 'error': trace.error})
            # Failed calls can be billed without returning usage. Never label that cost complete.
            complete = not errors and not usage.missing and usage.responses > 0
            row = dict(config=config, split=split, model=model, labels_from=label_source,
                       ts=datetime.now(UTC).isoformat(),
                       comment_ids=[label['comment_id'] for label in labels], n=len(labels),
                       scores=score_rows(pairs), tokens=usage.tokens, rates_usd_per_mtok=rates,
                       price_source=source, cost_complete=complete, errors=errors,
                       usage_missing=usage.missing, model_responses=usage.responses,
                       cost_usd=sum(usage.tokens[k] * rates[k] for k in rates) / 1_000_000,
                       p50_ms=statistics.median(latencies),
                       p95_ms=sorted(latencies)[math.ceil(len(latencies) * .95) - 1])
            rows.append(row)
            print(f'{config} / {split}: {len(labels)} posts, {len(errors)} errors', flush=True)

    lines = ['# LLM cost vs quality', '', f'Model: {model}. Pricing source: {source}.', '',
             'Unweighted labeled-set scores; parentheses contain 95% Wilson intervals. '
             'Skills macro-F1 has no Wilson interval. Costs are USD.', '']
    for config in ('B', 'C', 'D', 'E', 'W'):
        selected = [r for r in rows if r['config'] == config]
        lines += [f'## Config {config}', '']
        headers = [f"{r['split'].capitalize()} (n={r['n']})" for r in selected]
        lines += ['| Field | ' + ' | '.join(headers) + ' | Halluc, ' + selected[-1]['split'] + ' |',
                  '| --- | ' + ' | '.join('---' for _ in selected) + ' | ---: |']
        for field in ('company', 'salary', 'location', 'skills', 'remote', 'seniority'):
            cells = []
            for row in selected:
                score = row['scores'][field]
                if 'precision' in score:
                    lo, hi = score['precision_ci95']
                    cells.append(f"{score['precision']:.1%} ({lo*100:.0f} to {hi*100:.0f})")
                elif field == 'skills':
                    cells.append(f"{score['macro_f1']:.3f}")
                else:
                    cells.append(f"{score['accuracy']:.1%} accuracy")
            halluc = selected[-1]['scores'][field].get('hallucination_rate')
            lines.append('| ' + ('skills F1' if field == 'skills' else field) + ' | '
                         + ' | '.join(cells) + ' | '
                         + (f'{halluc:.1%}' if halluc is not None else '') + ' |')
        for title, key, fmt in [('Cost, USD', 'cost_usd', '.6f'),
                                ('p50 latency, ms', 'p50_ms', '.1f'),
                                ('p95 latency, ms', 'p95_ms', '.1f')]:
            cells = [format(r[key], fmt) + (' (incomplete)' if key == 'cost_usd'
                     and not r['cost_complete'] else '') for r in selected]
            lines.append('| ' + title + ' | ' + ' | '.join(cells) + ' | |')
        lines.append('')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text('\n'.join(lines) + '\n')
    detail.write_text(json.dumps(rows, indent=2) + '\n')
    print(f'Wrote {args.output} and {detail}')
    if any(not row['cost_complete'] for row in rows):
        raise SystemExit('Some calls failed or returned invalid/missing usage. '
                         'See JSON errors and usage_missing; costs are incomplete.')


if __name__ == '__main__':
    main()
