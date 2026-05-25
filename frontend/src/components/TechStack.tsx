const technologies = [
  'LangChain',
  'LlamaIndex',
  'OpenAI',
  'Anthropic',
  'HuggingFace',
  'ChromaDB',
  'Qdrant',
  'PGVector',
  'Docker',
  'FastAPI',
];

export function TechStack() {
  return (
    <section className="py-24 border-t border-white/5 bg-black/50 overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-12 text-center">
        <p className="text-sm font-semibold tracking-wider text-indigo-400 uppercase">
          Поддерживаемые технологии и интеграции
        </p>
      </div>

      <div className="max-w-5xl mx-auto px-4 flex flex-wrap justify-center gap-x-12 gap-y-6 sm:gap-x-16">
        {technologies.map((tech) => (
          <span
            key={tech}
            className="text-xl sm:text-2xl font-bold text-white/20 hover:text-white/40 transition-colors duration-300"
          >
            {tech}
          </span>
        ))}
      </div>
    </section>
  );
}
