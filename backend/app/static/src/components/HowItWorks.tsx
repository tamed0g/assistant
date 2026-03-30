import { motion } from 'framer-motion';
import { Database, FileText, Bot, BrainCircuit } from 'lucide-react';

const steps = [
  {
    title: "Импорт данных",
    description: "Подключите свою базу знаний, документацию (PDF, TXT, Markdown) или корпоративные базы (Notion, Confluence).",
    icon: FileText,
  },
  {
    title: "Векторизация",
    description: "Ассистент разбивает текст на чанки и переводит в эмбеддинги с помощью моделей OpenAI или HuggingFace.",
    icon: Database,
  },
  {
    title: "Поиск контекста (Retrieval)",
    description: "На основе запроса пользователя система мгновенно находит самые релевантные куски информации в Vector DB.",
    icon: BrainCircuit,
  },
  {
    title: "Точная генерация",
    description: "LLM получает вопрос вместе с вашим контекстом и генерирует точный ответ без галлюцинаций.",
    icon: Bot,
  },
];

export function HowItWorks() {
  return (
    <section className="py-24 bg-black relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl mb-4">
            Прозрачная архитектура RAG
          </h2>
          <p className="text-xl text-zinc-400">
            Полноценный пайплайн поиска и генерации ответов, развернутый локально или в облаке. Никаких "черных ящиков".
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <motion.div
                key={step.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="relative"
              >
                {/* Connection line between steps (desktop only) */}
                {index !== steps.length - 1 && (
                  <div className="hidden md:block absolute top-8 left-[60%] w-[80%] h-[2px] bg-gradient-to-r from-indigo-500/50 to-transparent z-0" />
                )}
                
                <div className="relative z-10 flex flex-col items-center text-center group">
                  <div className="w-16 h-16 rounded-2xl bg-zinc-900/80 border border-white/5 flex items-center justify-center mb-6 group-hover:border-indigo-500/50 transition-colors duration-300 shadow-[0_0_15px_rgba(99,102,241,0.1)] group-hover:shadow-[0_0_25px_rgba(99,102,241,0.3)]">
                    <Icon className="w-8 h-8 text-indigo-400" />
                  </div>
                  <h3 className="text-lg font-bold text-white mb-3">
                    {index + 1}. {step.title}
                  </h3>
                  <p className="text-sm text-zinc-400 leading-relaxed">
                    {step.description}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
      
      {/* Background glow effect */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3/4 h-1/2 bg-indigo-500/10 blur-[120px] pointer-events-none rounded-full" />
    </section>
  );
}
