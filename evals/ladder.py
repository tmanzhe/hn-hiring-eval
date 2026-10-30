"""Run B, C, D, E and W on the same labels and write a Markdown quality/cost table."""

import argparse
import html
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
from evals.scorers import Outcome, score_set_pair
from ingest.corpus import by_id, to_text
from ingest.normalize import normalize


def build_disagreement_report(runs):
    """Build Markdown from (config, split, pairs) runs, using already-normalized predictions.

    Delegate matching to the existing scores block. Skills use the underlying pair scorer
    so rounding macro-F1 for display cannot hide a partial mismatch.
    """
    fields = ('company', 'salary', 'location', 'skills', 'remote', 'seniority')
    configs = ('B', 'C', 'D', 'E', 'W')
    grouped = {field: {config: [] for config in configs} for field in fields}

    def cell(value):
        encoded = html.escape(json.dumps(value, ensure_ascii=False)).replace('|', '&#124;')
        return f'<code>{encoded}</code>'

    for config, split, pairs in runs:
        for prediction, label in pairs:
            scores = score_rows([(prediction, label)])
            for field in fields:
                score = scores[field]
                if field == 'skills':
                    agrees = score_set_pair(prediction.skills, label.get('skills', []))[2] == 1
                elif 'outcomes' in score:
                    agrees = any(score['outcomes'].get(outcome.value, 0)
                                 for outcome in (Outcome.EXTRACTED, Outcome.ABSTAINED))
                else:
                    agrees = score['accuracy'] == 1
                if agrees:
                    continue
                if field == 'salary':
                    label_value = dict(min=label.get('salary_min'), max=label.get('salary_max'),
                                       period=label.get('salary_period') or 'year')
                    model_value = dict(min=prediction.salary_min, max=prediction.salary_max)
                else:
                    label_value = label.get(field, [] if field == 'skills' else None)
                    model_value = getattr(prediction, field)
                grouped[field][config].append(
                    f'| {split} | {cell(label["comment_id"])} | {cell(label_value)} '
                    f'| {cell(model_value)} |')

    lines = ['# LLM disagreements with Claude-drafted gold labels', '',
             'Audit these disagreements to check whether the labels favor Claude. '
             'Counts are disagreeing posts per field/config, pooled across selected splits.', '',
             '| Field | ' + ' | '.join(configs) + ' |',
             '| --- | ' + ' | '.join('---:' for _ in configs) + ' |']
    for field in fields:
        lines.append('| ' + field + ' | '
                     + ' | '.join(str(len(grouped[field][config])) for config in configs) + ' |')
    lines += ['', 'Only the six scored fields are included. Nullable extracted/abstained outcomes '
              'are agreements; skills disagree whenever normalized per-post F1 is below 1; '
              'enums use scorer accuracy. Label values are shown as recorded. '
              'Model values are the normalized predictions used for scoring; salary min/max '
              'are annualized, while the label retains its original period.', '']
    for field in fields:
        lines += [f'## {field}', '']
        for config in configs:
            entries = grouped[field][config]
            lines += [f'### Config {config} ({len(entries)})', '']
            if entries:
                lines += ['| Split | Post / label ID | Label value | Model value |',
                          '| --- | --- | --- | --- |', *entries, '']
            else:
                lines += ['No disagreements.', '']
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--split', choices=['dev', 'held-out', 'all'], default='dev')
    ap.add_argument('--limit', type=int, help='first N labeled posts per selected split')
    ap.add_argument('--output', type=Path, default=Path('evals/cost-quality.md'))
    ap.add_argument('--disagreements', nargs='?', type=Path,
                    const=Path('evals/disagreements.md'), metavar='PATH',
                    help='write a gold-label disagreement report (default: evals/disagreements.md)')
    args = ap.parse_args()
    if args.limit is not None and args.limit <= 0:
        ap.error('--limit must be positive')
    if args.output.suffix.lower() != '.md':
        ap.error('--output must end in .md; the JSON details use the same stem with .json')
    detail = args.output.with_suffix('.json')
    if args.output.is_dir() or detail.is_dir():
        ap.error('--output and its .json companion must be file paths, not directories')
    if args.disagreements is not None:
        if args.disagreements.is_dir():
            ap.error('--disagreements must be a file path, not a directory')
        if args.disagreements.resolve() in (args.output.resolve(), detail.resolve()):
            ap.error('--disagreements must differ from --output and its .json companion')
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
    disagreement_runs = []
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
            if args.disagreements is not None:
                disagreement_runs.append((config, split, pairs))
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
    if args.disagreements is not None:
        args.disagreements.parent.mkdir(parents=True, exist_ok=True)
        args.disagreements.write_text(build_disagreement_report(disagreement_runs), encoding='utf-8')
        print(f'Wrote {args.disagreements}')
    if any(not row['cost_complete'] for row in rows):
        raise SystemExit('Some calls failed or returned invalid/missing usage. '
                         'See JSON errors and usage_missing; costs are incomplete.')


if __name__ == '__main__':
    main()
