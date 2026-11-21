export default function AboutPage() {
  return (
    <div className="prose mx-auto max-w-3xl space-y-3 px-4 py-6 text-slate-700">
      <h2 className="text-xl font-semibold text-slate-900">About SarkariSathi AI</h2>
      <p>A multilingual (English / हिंदी / मराठी) retrieval-augmented assistant for Indian government schemes. Every answer is built only from indexed documents, carries citations, and the assistant says so when the documents do not contain the answer.</p>
      <p>Pipeline: language detection → hybrid retrieval (BM25 + char n-gram + dense, RRF) → optional reranker → relevance check → grounded generation → citation verification.</p>
      <p className="rounded bg-amber-50 p-3 text-amber-900">This is information, not legal or official advice. Scheme rules change; always confirm on the official portal before applying. Bundled documents are sample summaries unless your deployment ingested official PDFs.</p>
    </div>
  )
}
