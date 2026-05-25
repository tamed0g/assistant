import { ArrowRight, BookText } from 'lucide-react';

export function Hero() {
  return (
    <section className="relative pt-32 pb-20 md:pt-48 md:pb-32 overflow-hidden">
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] opacity-20 pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 to-purple-500 blur-[100px] rounded-full" />
      </div>

      <div className="relative z-10 mx-auto max-w-7xl px-6 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-sm text-indigo-300 mb-8">
          <span className="flex h-2 w-2 rounded-full bg-indigo-500 animate-pulse" />
          Enterprise RAG Architecture
        </div>

        <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-white mb-8">
          Your Data. <br className="hidden md:block" />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">
            Uncompromised AI.
          </span>
        </h1>

        <p className="text-lg md:text-xl text-zinc-400 max-w-2xl mx-auto mb-10">
          A production-ready Enterprise RAG AI Assistant. Connect your internal knowledge bases securely and deploy a highly contextual AI that understands your business.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <a
            href="#integration"
            className="w-full sm:w-auto flex items-center justify-center gap-2 bg-indigo-500 hover:bg-indigo-400 text-white px-6 py-3 rounded-lg font-medium transition-colors"
          >
            Get Started <ArrowRight className="w-4 h-4" />
          </a>

          <a
            href="https://github.com/tamed0g/assistant"
            target="_blank"
            rel="noreferrer"
            className="w-full sm:w-auto flex items-center justify-center gap-2 bg-white/5 hover:bg-white/10 text-white px-6 py-3 rounded-lg font-medium transition-colors border border-white/10"
          >
            <BookText className="w-4 h-4" /> GitHub
          </a>
        </div>
      </div>
    </section>
  );
}
