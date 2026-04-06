import { TerminalSquare } from 'lucide-react';

export function Footer() {
  return (
    <footer className="border-t border-white/5 py-12 bg-black">
      <div className="mx-auto max-w-7xl px-6 flex flex-col md:flex-row items-center justify-between">
        <div className="flex items-center gap-2 text-white font-medium mb-4 md:mb-0">
          <TerminalSquare className="w-5 h-5 text-indigo-400" />
          <span>ассистент</span>
        </div>
        
        <div className="text-sm text-zinc-500">
          Для приватности. Открытый исходный код под лицензией MIT.
        </div>
        
        <div className="flex gap-6 mt-4 md:mt-0 text-sm text-zinc-400">
          <a href="https://github.com/tamed0g/assistant" className="hover:text-white transition-colors">GitHub</a>
          <a href="#" className="hover:text-white transition-colors">Документация</a>
          <a href="#" className="hover:text-white transition-colors">Discord</a>
        </div>
      </div>
    </footer>
  );
}