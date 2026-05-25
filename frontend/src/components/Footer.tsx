import { TerminalSquare } from 'lucide-react';

export function Footer() {
  return (
    <footer className="border-t border-white/5 py-12 bg-black">
      <div className="mx-auto max-w-7xl px-6 flex flex-col md:flex-row items-center justify-between">
        <div className="flex items-center gap-2 text-white font-medium mb-4 md:mb-0">
          <TerminalSquare className="w-5 h-5 text-indigo-400" />
          <span>ассистент</span>
        </div>
      </div>
    </footer>
  );
}