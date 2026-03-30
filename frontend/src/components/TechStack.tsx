import { motion } from 'framer-motion';

const technologies = [
  "LangChain",
  "LlamaIndex",
  "OpenAI",
  "Anthropic",
  "HuggingFace",
  "ChromaDB",
  "Qdrant",
  "PGVector",
  "Docker",
  "FastAPI"
];

export function TechStack() {
  return (
    <section className="py-24 border-t border-white/5 bg-black/50 overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-12 text-center">
        <p className="text-sm font-semibold tracking-wider text-indigo-400 uppercase">
          Поддерживаемые технологии и интеграции
        </p>
      </div>
      
      {/* Infinite marquee effect container */}
      <div className="relative flex overflow-x-hidden">
        {/* Gradient masks for smooth fading at the edges */}
        <div className="absolute inset-y-0 left-0 w-32 bg-gradient-to-r from-black to-transparent z-10"></div>
        <div className="absolute inset-y-0 right-0 w-32 bg-gradient-to-l from-black to-transparent z-10"></div>
        
        <motion.div
          className="flex whitespace-nowrap gap-12 sm:gap-24 px-6 items-center"
          animate={{
            x: ["0%", "-50%"],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "linear",
          }}
        >
          {/* Duplicate the array to create a seamless loop */}
          {[...technologies, ...technologies].map((tech, index) => (
            <span 
              key={index} 
              className="text-xl sm:text-2xl font-bold text-white/20 hover:text-white/40 transition-colors duration-300"
            >
              {tech}
            </span>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
