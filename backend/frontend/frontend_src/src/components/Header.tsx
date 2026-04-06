import { TerminalSquare } from 'lucide-react';

export function Header() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 bg-black/50 backdrop-blur-md">
      <div className="mx-auto max-w-7xl px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2 text-white font-medium">
          <TerminalSquare className="w-5 h-5 text-indigo-400" />
          <span>ассистент</span>
        </div>
      </div>
    </header>
  );
}