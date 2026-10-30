import type { ReactNode } from "react";

export default function EmptyState({ title, children, command, prerequisite }: {
  title: string;
  children: ReactNode;
  command: string;
  prerequisite?: string;
}) {
  return (
    <div className="empty-state">
      <span className="eyebrow">Waiting for a local report</span>
      <h3 className="mt-3 text-xl font-semibold text-slate-900">{title}</h3>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-7 text-slate-600">{children}</p>
      <details className="developer-details mx-auto mt-5 max-w-2xl text-left">
        <summary>For developers: generate this report</summary>
        <div className="mt-4 space-y-3 text-sm text-slate-600">
          <p>Run from the repository root, then rebuild the dashboard.</p>
          {prerequisite && <p>{prerequisite}</p>}
          <pre><code>{command}</code></pre>
        </div>
      </details>
    </div>
  );
}
