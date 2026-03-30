import { motion } from 'framer-motion';
import { Database, Shield, Cpu, Zap, Link, Box } from 'lucide-react';

const features = [
  {
    icon: Database,
    title: 'Any Vector Database',
    description: 'Plug and play with Chroma, Pinecone, Qdrant or Milvus. Store your embeddings where you want.',
  },
  {
    icon: Shield,
    title: 'Enterprise Security',
    description: 'Data never leaves your servers. Role-based access control, strict privacy boundaries, and SSO ready.',
  },
  {
    icon: Cpu,
    title: 'Local & Cloud LLMs',
    description: 'Connect to OpenAI, Anthropic, or run entirely offline with local models using Ollama and LM Studio.',
  },
  {
    icon: Zap,
    title: 'Retrieval-Augmented',
    description: 'No more hallucinations. The AI grounds every response with actual citations from your internal docs.',
  },
  {
    icon: Link,
    title: 'API-First Design',
    description: 'Easily integrate the assistant into your existing slack, teams, or internal portals via RESTful APIs.',
  },
  {
    icon: Box,
    title: 'Docker Ready',
    description: 'Deploy the entire stack in minutes with our comprehensive docker-compose configuration.',
  }
];

export function Features() {
  return (
    <section id="features" className="py-24 bg-zinc-950">
      <div className="mx-auto max-w-7xl px-6">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-white mb-4">
            Built for Scale and Privacy
          </h2>
          <p className="text-zinc-400 max-w-2xl mx-auto">
            Everything you need to run a production-grade AI assistant over your internal knowledge base without sending sensitive data to third parties.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, i) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                className="group relative rounded-2xl border border-white/5 bg-white/5 p-8 hover:bg-white/10 transition-colors"
              >
                <div className="mb-6 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-400 group-hover:bg-indigo-500/20 transition-colors">
                  <Icon className="h-6 w-6" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">
                  {feature.title}
                </h3>
                <p className="text-zinc-400 leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}