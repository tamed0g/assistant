import { FormEvent, useMemo, useState } from 'react';

function App() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState<string[]>([]);
  const [conversationId, setConversationId] = useState('');
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

  const askQuestion = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!question.trim()) return;

    setChatLoading(true);
    setChatError('');

    try {
      const response = await fetch('/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: question.trim(),
          conversation_id: effectiveConversationId,
        }),
      });

      if (!response.ok) {
        const errorBody = await response.text();
        throw new Error(errorBody || `Request failed: ${response.status}`);
      }

      const data = await response.json();
      setAnswer(data.answer ?? '');
      setSources(Array.isArray(data.sources) ? data.sources : []);
    } catch (error) {
      setChatError(error instanceof Error ? error.message : 'Unknown error while asking a question.');
      setAnswer('');
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
        const errorBody = await response.text();
        throw new Error(errorBody || `Upload failed: ${response.status}`);
      }

      const data = await response.json();
      setUploadMessage(
        `Uploaded "${data.filename}" successfully (${data.chunks_count} chunks).`,
      );
      setFile(null);
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Unknown error while uploading.');
    } finally {
      setUploadLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 selection:bg-indigo-500/30 font-sans">
      <main className="mx-auto max-w-5xl px-4 py-10 sm:px-6 sm:py-14">
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
          Enterprise Assistant
        </h1>
        <p className="mt-3 text-zinc-400">
          Upload internal docs and chat with your knowledge base.
        </p>

        <div className="mt-8 grid gap-6 lg:grid-cols-2">
          <section className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <h2 className="text-xl font-semibold">1) Upload Document</h2>
            <p className="mt-2 text-sm text-zinc-400">
              Supported formats: .txt, .pdf, .md
            </p>

            <form onSubmit={uploadDocument} className="mt-4 space-y-4">
              <input
                type="file"
                accept=".txt,.pdf,.md"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                className="block w-full rounded-lg border border-zinc-700 bg-zinc-950 p-2 text-sm"
              />

              <button
                type="submit"
                disabled={!file || uploadLoading}
                className="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {uploadLoading ? 'Uploading...' : 'Upload'}
              </button>
            </form>

            {uploadMessage && <p className="mt-4 text-sm text-emerald-400">{uploadMessage}</p>}
            {uploadError && <p className="mt-4 text-sm text-red-400">{uploadError}</p>}
          </section>

          <section className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <h2 className="text-xl font-semibold">2) Ask Question</h2>
            <p className="mt-2 text-sm text-zinc-400">
              Leave conversation ID empty to auto-generate one.
            </p>

            <form onSubmit={askQuestion} className="mt-4 space-y-4">
              <input
                type="text"
                value={conversationId}
                onChange={(event) => setConversationId(event.target.value)}
                placeholder="Conversation ID (optional)"
                className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
              />

              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Ask something about your uploaded documents..."
                className="h-28 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
                required
              />

              <button
                type="submit"
                disabled={chatLoading}
                className="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {chatLoading ? 'Thinking...' : 'Ask'}
              </button>
            </form>

            {chatError && <p className="mt-4 text-sm text-red-400">{chatError}</p>}

            {answer && (
              <div className="mt-5 rounded-lg border border-zinc-700 bg-zinc-950 p-4">
                <h3 className="font-semibold text-zinc-200">Answer</h3>
                <p className="mt-2 whitespace-pre-wrap text-sm text-zinc-300">{answer}</p>

                {sources.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-medium text-zinc-200">Sources</h4>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-zinc-400">
                      {sources.map((source, index) => (
                        <li key={`${source}-${index}`}>{source}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}

export default App;
