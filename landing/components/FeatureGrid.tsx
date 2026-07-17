/**
 * Cost Melt Landing - Feature Grid Component
 * 
 * Grid of 6 features with icons, titles, descriptions, and hover animations.
 */

'use client';

import { motion } from 'framer-motion';
import {
  Route,
  Database,
  Shrink,
  Layers,
  BarChart3,
  Zap
} from 'lucide-react';
import Section from './Section';

const features = [
  {
    icon: Route,
    title: 'Smart Model Routing',
    description: 'Automatically chooses the cheapest capable model (OpenAI, Anthropic, Groq, DeepSeek).',
    color: 'from-[#2F6DAB] to-[#1C3F70]',
  },
  {
    icon: Database,
    title: 'Semantic Caching',
    description: 'Identifies similar prompts to return instant cached responses.',
    color: 'from-[#00E0FF] to-[#2F6DAB]',
  },
  {
    icon: Shrink,
    title: 'Prompt Compression',
    description: 'Shrinks prompt tokens 20–50% before sending.',
    color: 'from-[#1C3F70] to-[#2F6DAB]',
  },
  {
    icon: Layers,
    title: 'Micro-Batching',
    description: 'Groups simultaneous requests for massive throughput improvements.',
    color: 'from-[#2F6DAB] to-[#00E0FF]',
  },
  {
    icon: BarChart3,
    title: 'Cost Analytics Dashboard',
    description: 'Visualize requests, routing, savings, and cache performance.',
    color: 'from-[#00E0FF] to-[#1C3F70]',
  },
  {
    icon: Zap,
    title: '5-Minute Integration',
    description: 'Drop-in middleware or simple REST proxy.',
    color: 'from-[#1C3F70] to-[#00E0FF]',
  },
];

const container = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
    },
  },
};

export default function FeatureGrid() {
  return (
    <Section className="bg-[#0B1221]">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
        className="text-center mb-16"
      >
        <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
          Everything You Need to Cut Costs
        </h2>
        <p className="text-xl text-gray-400 max-w-2xl mx-auto">
          Powerful features that work together to maximize your savings
        </p>
      </motion.div>

      <motion.div
        variants={container}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
      >
        {features.map((feature, index) => {
          const Icon = feature.icon;
          return (
            <motion.div
              key={index}
              variants={item}
              whileHover={{ y: -8, scale: 1.02 }}
              className="group relative bg-[#1a2332] border border-[#2F6DAB]/20 rounded-xl p-8 hover:border-[#2F6DAB]/50 transition-all duration-300"
            >
              {/* Gradient Background on Hover */}
              <div
                className={`absolute inset-0 bg-gradient-to-br ${feature.color} opacity-0 group-hover:opacity-10 rounded-xl transition-opacity duration-300`}
              />

              <div className="relative z-10">
                <div
                  className={`w-14 h-14 bg-gradient-to-br ${feature.color} rounded-lg flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}
                >
                  <Icon className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-xl font-bold text-white mb-3">
                  {feature.title}
                </h3>
                <p className="text-gray-400 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </motion.div>
          );
        })}
      </motion.div>
    </Section>
  );
}

