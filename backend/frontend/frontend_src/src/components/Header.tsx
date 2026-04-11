import { Github, TerminalSquare } from 'lucide-react';

const GITHUB_URL = 'https://github.com/tamed0g/assistant';

export function Header() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 bg-black/50 backdrop-blur-md">
      <div className="mx-auto max-w-7xl px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2 text-white font-medium">
          <TerminalSquare className="w-5 h-5 text-indigo-400" />
          <span>ассистент</span>
        </div>
        <a
          href={GITHUB_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-zinc-200 transition-colors hover:bg-white/10 hover:text-white"
        >
          <Github className="h-4 w-4" />
          GitHub
        </a>
      </div>
    </header>
  );
}