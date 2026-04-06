import { FormEvent, useEffect, useMemo, useState } from 'react';
import { Header } from './components/Header';
import { Footer } from './components/Footer';

function App() {
  type ChatMessage = { role: 'user' | 'assistant'; content: string };
  type DocumentInfo = { filename: string; chunks: number };

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

  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [docsError, setDocsError] = useState('');

  const [conversations, setConversations] = useState<string[]>([]);
  const [conversationsLoading, setConversationsLoading] = useState(false);
  const [conversationsError, setConversationsError] = useState('');

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
      void refreshDocuments();
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Unknown error while uploading.');
    } finally {
      setUploadLoading(false);
    }
  };

  const refreshDocuments = async () => {
    setDocsLoading(true);
    setDocsError('');
    try {
      const resp = await fetch('/documents');
      if (!resp.ok) {
        throw new Error(await resp.text());
      }
      const data = await resp.json();
      setDocuments(Array.isArray(data.documents) ? data.documents : []);
    } catch (e) {
      setDocsError(e instanceof Error ? e.message : 'Не удалось загрузить список документов.');
    } finally {
      setDocsLoading(false);
    }
  };

  const deleteDoc = async (filename: string) => {
    if (!confirm(`Удалить документ "${filename}"?`)) return;
    try {
      const resp = await fetch(`/documents/${encodeURIComponent(filename)}`, { method: 'DELETE' });
      if (!resp.ok) throw new Error(await resp.text());
      await refreshDocuments();
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Не удалось удалить документ.');
    }
  };

  const deleteAllDocs = async () => {
    if (!confirm('Удалить все документы?')) return;
    try {
      const resp = await fetch('/documents', { method: 'DELETE' });
      if (!resp.ok) throw new Error(await resp.text());
      await refreshDocuments();
      setUploadMessage('');
      setUploadError('');
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Не удалось удалить все документы.');
    }
  };

  const refreshConversations = async () => {
    setConversationsLoading(true);
    setConversationsError('');
    try {
      const resp = await fetch('/conversations');
      if (!resp.ok) throw new Error(await resp.text());
      const data = await resp.json();
      setConversations(Array.isArray(data.conversations) ? data.conversations : []);
    } catch (e) {
      setConversationsError(e instanceof Error ? e.message : 'Не удалось загрузить список диалогов.');
    } finally {
      setConversationsLoading(false);
    }
  };

  const openConversation = async (id: string) => {
    setConversationId(id);
    setSources([]);
    setSourcesOpen(false);
    setChatError('');
    try {
      const resp = await fetch(`/conversations/${encodeURIComponent(id)}`);
      if (!resp.ok) throw new Error(await resp.text());
      const data = await resp.json();
      const msgs = Array.isArray(data.messages) ? data.messages : [];
      setMessages(
        msgs
          .filter((m: any) => m && (m.role === 'user' || m.role === 'assistant') && typeof m.content === 'string')
          .map((m: any) => ({ role: m.role, content: m.content })) as ChatMessage[],
      );
    } catch (e) {
      setChatError(e instanceof Error ? e.message : 'Не удалось открыть диалог.');
    }
  };

  const deleteConversationById = async (id: string) => {
    if (!confirm(`Удалить диалог "${id}"?`)) return;
    try {
      const resp = await fetch(`/conversations/${encodeURIComponent(id)}`, { method: 'DELETE' });
      if (!resp.ok) throw new Error(await resp.text());
      if (conversationId.trim() === id) {
        setConversationId('');
        setMessages([]);
        try {
          window.localStorage.removeItem('conversation_id');
        } catch {
          // ignore
        }
      }
      await refreshConversations();
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Не удалось удалить диалог.');
    }
  };

  useEffect(() => {
    void refreshDocuments();
    void refreshConversations();
  }, []);

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
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-lg font-semibold">Документы</h2>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => void refreshDocuments()}
                    className="rounded-lg border border-white/10 bg-black/20 px-3 py-1.5 text-sm text-zinc-200 hover:bg-black/30"
                    disabled={docsLoading}
                  >
                    {docsLoading ? '...' : 'Обновить'}
                  </button>
                  <button
                    type="button"
                    onClick={() => void deleteAllDocs()}
                    className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-1.5 text-sm text-red-200 hover:bg-red-500/20"
                  >
                    Удалить все
                  </button>
                </div>
              </div>

              {docsError && <div className="mt-3 text-sm text-red-200">{docsError}</div>}

              <div className="mt-3 space-y-2">
                {documents.length === 0 ? (
                  <div className="text-sm text-zinc-400">Пока нет загруженных документов.</div>
                ) : (
                  documents.map((d) => (
                    <div key={d.filename} className="flex items-center justify-between gap-3 rounded-lg border border-white/10 bg-black/20 px-3 py-2">
                      <div className="min-w-0">
                        <div className="truncate text-sm text-zinc-100">{d.filename}</div>
                        <div className="text-xs text-zinc-500">чанков: {d.chunks}</div>
                      </div>
                      <button
                        type="button"
                        onClick={() => void deleteDoc(d.filename)}
                        className="rounded-md border border-red-500/30 bg-red-500/10 px-2.5 py-1 text-xs text-red-200 hover:bg-red-500/20"
                      >
                        Удалить
                      </button>
                    </div>
                  ))
                )}
              </div>
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
                    void refreshConversations();
                  }}
                  className="w-full rounded-lg border border-white/10 bg-black/20 px-4 py-2 text-sm text-zinc-200 hover:bg-black/30"
                >
                  Начать новый диалог
                </button>
              </div>
            </div>

            <div className="mt-4 rounded-xl border border-white/10 bg-zinc-950/60 p-4">
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-lg font-semibold">Диалоги</h2>
                <button
                  type="button"
                  onClick={() => void refreshConversations()}
                  className="rounded-lg border border-white/10 bg-black/20 px-3 py-1.5 text-sm text-zinc-200 hover:bg-black/30"
                  disabled={conversationsLoading}
                >
                  {conversationsLoading ? '...' : 'Обновить'}
                </button>
              </div>

              {conversationsError && <div className="mt-3 text-sm text-red-200">{conversationsError}</div>}

              <div className="mt-3 space-y-2">
                {conversations.length === 0 ? (
                  <div className="text-sm text-zinc-400">Пока нет сохранённых диалогов.</div>
                ) : (
                  conversations.map((id) => (
                    <div key={id} className="flex items-center justify-between gap-2 rounded-lg border border-white/10 bg-black/20 px-3 py-2">
                      <button
                        type="button"
                        onClick={() => void openConversation(id)}
                        className="min-w-0 flex-1 truncate text-left text-sm text-zinc-100 hover:text-white"
                        title={id}
                      >
                        {id}
                      </button>
                      <button
                        type="button"
                        onClick={() => void deleteConversationById(id)}
                        className="rounded-md border border-red-500/30 bg-red-500/10 px-2.5 py-1 text-xs text-red-200 hover:bg-red-500/20"
                      >
                        Удалить
                      </button>
                    </div>
                  ))
                )}
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
