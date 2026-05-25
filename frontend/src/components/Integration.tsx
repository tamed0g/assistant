import { Copy, Terminal } from 'lucide-react';

const codeSnippet = `git clone https://github.com/tamed0g/assistant.git
cd assistant

# Setup your environment variables
cp .env.example .env
nano .env

# Deploy with Docker Compose
docker-compose up -d --build

# Your Enterprise RAG Assistant is now running at localhost:3000`;

export function Integration() {
  return (
    <section id="integration" className="py-24 bg-black overflow-hidden relative border-t border-zinc-900">
      <div className="mx-auto max-w-7xl px-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <div>
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-white mb-6">
              Deploy in Minutes
            </h2>
            <p className="text-lg text-zinc-400 mb-8">
              Don't spend weeks building a RAG pipeline from scratch. Our dockerized setup gets your enterprise assistant running locally or in your cloud environment in under 5 minutes.
            </p>

            <ul className="space-y-4 mb-8">
              {[
                '100% Open Source and self-hostable',
                'Built-in web UI for chatting with documents',
                'Easily ingest PDFs, Notion pages, and URLs',
                'Configurable prompts and retrieval settings',
              ].map((item, i) => (
                <li key={i} className="flex items-center gap-3 text-zinc-300">
                  <div className="flex-shrink-0 w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center text-xs">✓</div>
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="relative">
            <div className="absolute -inset-1 rounded-2xl bg-gradient-to-r from-indigo-500 to-purple-600 opacity-20 blur-xl" />
            <div className="relative rounded-2xl border border-white/10 bg-[#0d0d0d] overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 bg-white/5">
                <div className="flex gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/50" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500/20 border border-yellow-500/50" />
                  <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/50" />
                </div>
                <div className="flex items-center gap-2 text-xs text-zinc-500 font-mono">
                  <Terminal className="w-3 h-3" /> bash
                </div>
                <button
                  type="button"
                  className="p-1.5 rounded-md hover:bg-white/10 text-zinc-400 transition-colors"
                  aria-label="Copy code"
                >
                  <Copy className="w-4 h-4" />
                </button>
              </div>
              <div className="p-6 overflow-x-auto">
                <pre className="text-sm font-mono text-indigo-200">
                  <code>{codeSnippet}</code>
                </pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
