"use client";

import { useMemo, useRef, useState } from "react";
import Link from "next/link";
import {
  Background, BackgroundVariant, Controls, Handle, MarkerType, Position, ReactFlow,
  type Edge, type Node, type NodeProps,
} from "@xyflow/react";
import type { PipelineStep } from "../lib/pipeline";
import "@xyflow/react/dist/style.css";

type StepNode = Node<{
  step: PipelineStep;
  index: number;
  input: Position;
  output: Position;
}, "pipeline">;

function PipelineNode({ data, selected }: NodeProps<StepNode>) {
  const { step, index, input, output } = data;
  return (
    <div className={`pipeline-node ${selected ? "is-selected" : ""} ${step.pending ? "is-pending" : ""}`}>
      {index > 0 && <Handle type="target" position={input} isConnectable={false} />}
      <div className="flex items-center justify-between gap-2">
        <span className={`pipeline-symbol ${step.id === "thread" ? "is-hn" : ""}`} aria-hidden="true">{step.symbol}</span>
        <span className="font-mono text-[11px] tracking-wider text-slate-400">STEP {String(index + 1).padStart(2, "0")}</span>
      </div>
      <div className="mt-3 flex items-center justify-between gap-2">
        <h3 className="text-[15px] font-semibold text-slate-950">{step.title}</h3>
        <span aria-hidden="true" className="text-slate-400">↗</span>
      </div>
      <p className="mt-1 text-xs text-slate-500">{step.summary}</p>
      <p className={`pipeline-node-status ${step.pending ? "is-pending" : ""}`}>
        <span aria-hidden="true" />{step.status}
      </p>
      {index < 6 && <Handle type="source" position={output} isConnectable={false} />}
    </div>
  );
}

const nodeTypes = { pipeline: PipelineNode };
// A single continuous path, in reading order, with room for an adjacent evidence panel.
const layout = [
  { x: 30, y: 30, input: Position.Left, output: Position.Right },
  { x: 360, y: 30, input: Position.Left, output: Position.Bottom },
  { x: 360, y: 245, input: Position.Top, output: Position.Left },
  { x: 30, y: 245, input: Position.Right, output: Position.Bottom },
  { x: 30, y: 460, input: Position.Top, output: Position.Right },
  { x: 360, y: 460, input: Position.Left, output: Position.Bottom },
  { x: 360, y: 675, input: Position.Top, output: Position.Bottom },
];

function StepEvidence({ step }: { step: PipelineStep }) {
  return (
    <div className="space-y-6 text-sm">
      <p className="leading-7 text-slate-600">{step.description}</p>
      <section aria-label={`${step.title}: committed evidence`}>
        <h3 className="eyebrow">Committed evidence</h3>
        {step.metrics.length > 0 && <dl className="mt-3 grid grid-cols-2 gap-3">
          {step.metrics.map((metric) => <div key={metric.label} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
            <dd className="text-2xl font-semibold tracking-tight text-slate-950 tabular-nums">{metric.value}</dd>
            <dt className="mt-1 text-xs leading-5 text-slate-500">{metric.label}</dt>
          </div>)}
        </dl>}
        <p className={`mt-3 rounded-xl border p-3 text-xs leading-6 ${step.pending ? "border-amber-200 bg-amber-50 text-amber-950" : "border-slate-200 bg-slate-50 text-slate-600"}`}>
          {step.note}
        </p>
        {step.table && <div className="pipeline-evidence-table mt-4" role="region" aria-label={step.table.caption} tabIndex={0}>
          <table>
            <caption>{step.table.caption}</caption>
            <thead><tr>{step.table.columns.map((column) => <th key={column} scope="col">{column}</th>)}</tr></thead>
            <tbody>{step.table.rows.map((row, index) => <tr key={index}>
              {row.map((cell, column) => column === 0
                ? <th key={column} scope="row">{cell}</th>
                : <td key={column} className="tabular-nums">{cell}</td>)}
            </tr>)}</tbody>
          </table>
        </div>}
        <p className="mt-3 break-words font-mono text-[10px] leading-5 text-slate-400">{step.source}</p>
      </section>

      <section className="border-t border-slate-100 pt-5" aria-label={`${step.title}: example post`}>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="eyebrow">One post, traced</h3>
          {step.example.id && <a className="text-link text-xs" href={`https://news.ycombinator.com/item?id=${encodeURIComponent(step.example.id)}`}>
            {step.example.title} ↗
          </a>}
        </div>
        <p className="mt-3 text-xs leading-6 text-slate-600">{step.example.note}</p>
        {step.example.content && <pre className="pipeline-example mt-3"><code>{step.example.content}</code></pre>}
        <p className="mt-3 break-words font-mono text-[10px] text-slate-400">{step.example.source}</p>
      </section>

      {step.id === "results" && <div className="flex flex-wrap gap-4 border-t border-slate-100 pt-4 text-xs">
        <Link href="/rungs" className="text-link">Evaluation ladder ↗</Link>
        <Link href="/disagreements" className="text-link">Label review ↗</Link>
      </div>}
    </div>
  );
}

export default function PipelineGraph({ steps }: { steps: PipelineStep[] }) {
  const [selected, setSelected] = useState<string | null>("rules");
  const panelRef = useRef<HTMLElement>(null);
  const active = steps.find((step) => step.id === selected);
  const nodes: StepNode[] = useMemo(() => steps.map((step, index) => ({
    id: step.id,
    type: "pipeline",
    position: { x: layout[index].x, y: layout[index].y },
    data: { step, index, input: layout[index].input, output: layout[index].output },
    selected: step.id === selected,
    draggable: false,
    ariaLabel: `Step ${index + 1}: ${step.title}. ${step.status}. Press Enter to inspect.`,
    domAttributes: { "aria-controls": "pipeline-inspector", "aria-expanded": step.id === selected },
  })), [steps, selected]);
  const edges: Edge[] = useMemo(() => steps.slice(1).map((step, index) => ({
    id: `${steps[index].id}-${step.id}`,
    source: steps[index].id,
    target: step.id,
    type: "smoothstep",
    animated: true,
    className: step.pending ? "pipeline-edge-pending" : "pipeline-edge-recorded",
    markerEnd: { type: MarkerType.ArrowClosed, color: step.pending ? "#a8b0bb" : "#56978e", width: 15, height: 15 },
    style: { stroke: step.pending ? "#a8b0bb" : "#56978e", strokeWidth: 1.5 },
  })), [steps]);

  function inspect(id: string) {
    setSelected(id);
    panelRef.current?.scrollTo({ top: 0 });
  }

  return (
    <section aria-label="Extraction pipeline" className="pipeline-shell">
      <div className="pipeline-toolbar">
        <p className="flex items-center gap-2 text-xs font-medium text-slate-700"><span className="h-2 w-2 rounded-full bg-teal-600" aria-hidden="true" />Extraction pipeline <span className="text-slate-400">/</span><span className="font-normal text-slate-500">Rung F</span></p>
        <div className="flex gap-4 text-[11px] text-slate-500" aria-label="Graph legend">
          <span className="flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-teal-600" aria-hidden="true" />Recorded</span>
          <span className="flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full border border-slate-400" aria-hidden="true" />Not run</span>
        </div>
      </div>

      <div className="pipeline-desktop">
        <div className="pipeline-canvas">
          <ReactFlow<StepNode>
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodeClick={(_, node) => inspect(node.id)}
            onKeyDownCapture={(event) => {
              const node = (event.target as HTMLElement).closest<HTMLElement>(".react-flow__node");
              if (node?.dataset.id && (event.key === "Enter" || event.key === " ")) {
                event.preventDefault();
                event.stopPropagation();
                inspect(node.dataset.id);
              }
              if (event.key === "Escape") setSelected(null);
            }}
            deleteKeyCode={null}
            nodesDraggable={false}
            nodesConnectable={false}
            edgesFocusable={false}
            fitView
            fitViewOptions={{ padding: 0.12, maxZoom: 1 }}
            minZoom={0.35}
            maxZoom={1.5}
            zoomOnScroll={false}
            preventScrolling={false}
            proOptions={{ hideAttribution: true }}
          >
            <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#d6dde5" />
            <Controls showInteractive={false} position="bottom-left" />
          </ReactFlow>
          <p className="pipeline-canvas-hint">Select a step · drag to pan · use + / − to zoom</p>
        </div>

        <aside id="pipeline-inspector" className="pipeline-inspector" ref={panelRef} aria-label="Step details">
          {active ? <>
            <div className="pipeline-inspector-heading">
              <div>
                <p className="eyebrow">Step {String(steps.indexOf(active) + 1).padStart(2, "0")} / {String(steps.length).padStart(2, "0")}</p>
                <h2 className="mt-2 text-2xl font-semibold text-slate-950">{active.title}</h2>
              </div>
              <button type="button" onClick={() => setSelected(null)} className="pipeline-close" aria-label="Close step details">×</button>
            </div>
            <div className="p-6"><StepEvidence key={active.id} step={active} /></div>
          </> : <div className="flex h-full flex-col items-center justify-center p-8 text-center">
            <span aria-hidden="true" className="mb-4 text-3xl text-orange-700">↖</span>
            <h2 className="text-lg font-semibold text-slate-900">Inspect a step</h2>
            <p className="mt-2 text-sm leading-7 text-slate-500">Select any node to see its committed evidence and example post.</p>
          </div>}
        </aside>
      </div>

      <ol className="pipeline-mobile" aria-label="Pipeline steps; tap to expand">
        {steps.map((step, index) => <li key={step.id}>
          <details open={step.id === selected}>
            <summary onClick={(event) => {
              event.preventDefault();
              setSelected((previous) => previous === step.id ? null : step.id);
            }}>
              <span className="pipeline-mobile-number" aria-hidden="true">{String(index + 1).padStart(2, "0")}</span>
              <span className="min-w-0 flex-1">
                <span className="block font-semibold text-slate-900">{step.title}</span>
                <span className="mt-1 block text-xs font-normal text-slate-500">{step.summary}</span>
                <span className={`pipeline-node-status ${step.pending ? "is-pending" : ""}`}><span aria-hidden="true" />{step.status}</span>
              </span>
              <span className="pipeline-mobile-chevron" aria-hidden="true">+</span>
            </summary>
            <div className="border-t border-slate-100 p-5"><StepEvidence step={step} /></div>
          </details>
          {index < steps.length - 1 && <span className="pipeline-mobile-connector" aria-hidden="true">↓</span>}
        </li>)}
      </ol>
    </section>
  );
}
