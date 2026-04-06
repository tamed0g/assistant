import { FormEvent, useMemo, useState } from 'react';
import { Header } from './components/Header';
import { Footer } from './components/Footer';

function App() {
  type ChatMessage = { role: 'user' | 'assistant'; content: string };

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState('');
  const [sources, setSources] = useState<string[]>([]);
  const [sourcesOpen, setSourcesOpen] = useState(false);

  const [conversationId, setConversationId] = useState(() => {
    try {
      const stored = window.localStorage.getItem('conversation_id');
      return stored ?? '';
    } catch {
      return '';
    }
  });

  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState('');

  const [file, setFile] = useState<File | null>(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState('');
  const [uploadError, setUploadError] = useState('');

  const effectiveConversationId = useMemo(() => {
    const trimmed = conversationId.trim();
    return trimmed || `session-${Date.now()}`;
  }, [conversationId]);

  const persistConversationId = (next: string) => {
    try {
      window.localStorage.setItem('conversation_id', next);
    } catch {
      // ignore storage errors
    }
  };

  const askQuestion = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!question.trim()) return;

    setChatLoading(true);
    setChatError('');
    setSourcesOpen(false);

    try {
      persistConversationId(effectiveConversationId);
      const userText = question.trim();
      setMessages((prev) => [...prev, { role: 'user', content: userText }]);

      const response = await fetch('/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: userText,
          conversation_id: effectiveConversationId,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        try {
          const parsed = JSON.parse(errorText);
          const detail = parsed?.detail ?? parsed?.message;
          throw new Error(detail || errorText || `Request failed: ${response.status}`);
        } catch {
          throw new Error(errorText || `Request failed: ${response.status}`);
        }
      }

      const data = await response.json();
      const assistantAnswer = data.answer ?? '';
      const assistantSources = Array.isArray(data.sources) ? (data.sources as unknown[]) : [];

      setSources(assistantSources.filter((s) => typeof s === 'string') as string[]);
      setMessages((prev) => [...prev, { role: 'assistant', content: assistantAnswer }]);
      setQuestion('');
    } catch (error) {
      const raw =
        error instanceof Error
          ? error.message
          : 'Unknown error while asking a question.';

      if (raw.includes('AI Generation service is currently unavailable')) {
        setChatError('Сервис генерации ответа временно недоступен. Попробуйте ещё раз через пару минут.');
      } else {
        setChatError(raw);
      }
      setSources([]);
    } finally {
      setChatLoading(false);
    }
  };

  const uploadDocument = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!file) return;

    setUploadLoading(true);
    setUploadError('');
    setUploadMessage('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        try {
          const parsed = JSON.parse(errorText);
          const detail = parsed?.detail ?? parsed?.message;
          throw new Error(detail || errorText || `Upload failed: ${response.status}`);
        } catch {
          throw new Error(errorText || `Upload failed: ${response.status}`);
        }
      }

      const data = await response.json();
      setUploadMessage(`Загружено "${data.filename}" успешно (${data.chunks_count} чанков).`);
      setFile(null);
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Unknown error while uploading.');
    } finally {
      setUploadLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white selection:bg-indigo-500/30 font-sans relative overflow-hidden">
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] opacity-20 pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 to-purple-500 blur-[100px] rounded-full" />
      </div>

      <Header />

      <main className="relative mx-auto max-w-7xl px-4 pt-28 pb-16 sm:px-6">
        <div className="flex flex-col lg:flex-row gap-6 lg:gap-10 items-start">
          <section className="w-full lg:w-[420px] rounded-2xl border border-white/10 bg-black/40 backdrop-blur p-5">
            <h1 className="text-2xl font-bold tracking-tight">Корпоративный помощник</h1>
            <p className="mt-2 text-sm text-zinc-400">
              Загружайте документы компании и задавайте вопросы — ответы будут опираться на ваш контент.
            </p>

            <div className="mt-6 rounded-xl border border-white/10 bg-zinc-950/60 p-4">
              <h2 className="text-lg font-semibold">1) Загрузить документ</h2>
              <p className="mt-1 text-sm text-zinc-400">Поддерживаются: `.txt`, `.pdf`, `.md`.</p>

              <form onSubmit={uploadDocument} className="mt-4">
                <div
                  className="rounded-xl border border-dashed border-white/20 bg-black/30 p-4"
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    const dropped = e.dataTransfer.files?.[0];
                    if (dropped) setFile(dropped);
                  }}
                >
                  <p className="text-sm text-zinc-300">
                    Перетащите файл сюда или выберите на компьютере.
                  </p>
                  <input
                    type="file"
                    accept=".txt,.pdf,.md"
                    onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                    className="mt-3 block w-full text-sm text-zinc-300 file:mr-3 file:rounded-md file:border-0 file:bg-indigo-600 file:px-3 file:py-2 file:text-white file:hover:bg-indigo-500"
                  />
                </div>

                <button
                  type="submit"
                  disabled={!file || uploadLoading}
                  className="mt-4 w-full rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {uploadLoading ? 'Загрузка...' : 'Загрузить'}
                </button>
              </form>

              {uploadMessage && <p className="mt-3 text-sm text-emerald-300">{uploadMessage}</p>}
              {uploadError && <p className="mt-3 text-sm text-red-300">{uploadError}</p>}
            </div>

            <div className="mt-4 rounded-xl border border-white/10 bg-zinc-950/60 p-4">
              <h2 className="text-lg font-semibold">2) Диалог</h2>
              <p className="mt-1 text-sm text-zinc-400">
                Можно оставить поле пустым — диалог создастся автоматически.
              </p>

              <div className="mt-3 space-y-3">
                <input
                  type="text"
                  value={conversationId}
                  onChange={(event) => setConversationId(event.target.value)}
                  placeholder="ID диалога (необязательно)"
                  className="w-full rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500"
                />

                <button
                  type="button"
                  onClick={() => {
                    setMessages([]);
                    setSources([]);
                    setSourcesOpen(false);
                    setConversationId('');
                    try {
                      window.localStorage.removeItem('conversation_id');
                    } catch {
                      // ignore
                    }
                  }}
                  className="w-full rounded-lg border border-white/10 bg-black/20 px-4 py-2 text-sm text-zinc-200 hover:bg-black/30"
                >
                  Начать новый диалог
                </button>
              </div>
            </div>
          </section>

          <section className="flex-1 w-full rounded-2xl border border-white/10 bg-black/40 backdrop-blur p-5">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold">Чат</h2>
              {sources.length > 0 && (
                <button
                  type="button"
                  onClick={() => setSourcesOpen((v) => !v)}
                  className="rounded-lg border border-white/10 bg-black/20 px-3 py-1.5 text-sm text-zinc-200 hover:bg-black/30"
                >
                  {sourcesOpen ? 'Скрыть источники' : `Показать источники (${sources.length})`}
                </button>
              )}
            </div>

            <div className="mt-4 h-[420px] overflow-y-auto rounded-xl border border-white/10 bg-zinc-950/50 p-4 space-y-4">
              {messages.length === 0 ? (
                <div className="text-sm text-zinc-400">
                  Напишите вопрос и нажмите «Спросить». Совет: сначала загрузите документ компании для более точных ответов.
                </div>
              ) : (
                messages.map((m, idx) => (
                  <div
                    key={`${m.role}-${idx}`}
                    className={m.role === 'user' ? 'flex justify-end' : 'flex justify-start'}
                  >
                    <div
                      className={
                        m.role === 'user'
                          ? 'max-w-[85%] rounded-2xl rounded-tr-md bg-indigo-600/30 border border-indigo-500/30 px-4 py-3 text-sm whitespace-pre-wrap'
                          : 'max-w-[85%] rounded-2xl rounded-tl-md bg-black/30 border border-white/10 px-4 py-3 text-sm text-zinc-100 whitespace-pre-wrap'
                      }
                    >
                      {m.content}
                    </div>
                  </div>
                ))
              )}
              {chatLoading && <div className="text-sm text-zinc-400">Ассистент печатает ответ...</div>}
            </div>

            {chatError && (
              <div className="mt-4 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                {chatError}
              </div>
            )}

            {sourcesOpen && sources.length > 0 && (
              <div className="mt-4 rounded-xl border border-white/10 bg-black/20 p-4">
                <div className="text-sm font-semibold text-zinc-200">Источники</div>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-zinc-300">
                  {sources.map((s, index) => (
                    <li key={`${s}-${index}`}>{s}</li>
                  ))}
                </ul>
              </div>
            )}

            <form onSubmit={askQuestion} className="mt-4 space-y-3">
              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Задайте вопрос по документам компании..."
                className="h-24 w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
                required
              />

              <div className="flex items-center gap-3">
                <button
                  type="submit"
                  disabled={chatLoading}
                  className="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {chatLoading ? 'Секундочку...' : 'Спросить'}
                </button>
                <div className="text-xs text-zinc-500">
                  Диалог ID: <span className="text-zinc-300">{effectiveConversationId}</span>
                </div>
              </div>
            </form>
          </section>
        </div>
      </main>

      <Footer />
    </div>
  );
}

export default App;
