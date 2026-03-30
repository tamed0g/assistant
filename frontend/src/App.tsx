import { Header } from './components/Header';
import { Hero } from './components/Hero';
import { Features } from './components/Features';
import { TechStack } from './components/TechStack';
import { HowItWorks } from './components/HowItWorks';
import { Integration } from './components/Integration';
import { Footer } from './components/Footer';

function App() {
  return (
    <div className="min-h-screen bg-black text-white selection:bg-indigo-500/30 font-sans">
      <Header />
      <main>
        <Hero />
        <Features />
        <TechStack />
        <HowItWorks />
        <Integration />
      </main>
      <Footer />
    </div>
  );
}

export default App;
