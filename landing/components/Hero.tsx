/**
 * Cost Melt Landing - Hero Component
 * 
 * Hero section with animated title, CTA buttons, and background gradients.
 */

'use client';

import { motion } from 'framer-motion';
import { ArrowRight, BookOpen } from 'lucide-react';
import Link from 'next/link';
import AnimatedText from './AnimatedText';

export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-[#0B1221]">
      {/* Animated Background Gradients */}
      <div className="absolute inset-0 overflow-hidden">
        <motion.div
          className="absolute top-0 left-1/4 w-96 h-96 bg-[#2F6DAB] rounded-full blur-3xl opacity-20"
          animate={{
            x: [0, 100, 0],
            y: [0, -50, 0],
            scale: [1, 1.2, 1],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
        <motion.div
          className="absolute bottom-0 right-1/4 w-96 h-96 bg-[#00E0FF] rounded-full blur-3xl opacity-10"
          animate={{
            x: [0, -100, 0],
            y: [0, 50, 0],
            scale: [1, 1.3, 1],
          }}
          transition={{
            duration: 25,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
        <motion.div
          className="absolute top-1/2 left-1/2 w-96 h-96 bg-[#1C3F70] rounded-full blur-3xl opacity-15"
          animate={{
            x: [0, 50, -50, 0],
            y: [0, -30, 30, 0],
            scale: [1, 1.1, 1],
          }}
          transition={{
            duration: 30,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      </div>

      {/* Content */}
      <div className="relative z-10 container mx-auto px-6 py-20 text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
            <AnimatedText text="Melt Your AI Costs By 40–70% — Automatically." />
          </h1>
        </motion.div>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-xl md:text-2xl text-gray-300 mb-12 max-w-3xl mx-auto leading-relaxed"
        >
          Cost Melt is the smartest LLM router, cache, and optimizer that cuts your token bills without changing your code.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <Link
            href="#start-free"
            className="group px-8 py-4 bg-gradient-to-r from-[#2F6DAB] to-[#1C3F70] text-white rounded-lg font-semibold text-lg hover:opacity-90 transition-opacity flex items-center gap-2 shadow-lg shadow-[#2F6DAB]/50"
          >
            Start Free
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
          <Link
            href="#docs"
            className="px-8 py-4 bg-[#0B1221] border-2 border-[#2F6DAB] text-white rounded-lg font-semibold text-lg hover:bg-[#2F6DAB]/10 transition-colors flex items-center gap-2"
          >
            <BookOpen className="w-5 h-5" />
            View Docs
          </Link>
        </motion.div>

        {/* Code Snippet Mockup */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.6 }}
          className="mt-16 max-w-2xl mx-auto"
        >
          <div className="bg-[#1a2332] border border-[#2F6DAB]/30 rounded-lg p-6 text-left shadow-2xl">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
              <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            </div>
            <pre className="text-sm text-gray-300 font-mono overflow-x-auto">
              <code>
                <span className="text-[#00E0FF]">import</span>{' '}
                <span className="text-white">costmelt</span>
                <br />
                <br />
                <span className="text-gray-500"># Replace your OpenAI endpoint</span>
                <br />
                <span className="text-white">client</span> ={' '}
                <span className="text-[#00E0FF]">costmelt</span>.
                <span className="text-yellow-400">Client</span>(
                <br />
                {'  '}
                <span className="text-green-400">api_key</span>=
                <span className="text-yellow-400">"your-key"</span>
                <br />
                )
                <br />
                <br />
                <span className="text-gray-500"># That's it! Automatic savings.</span>
              </code>
            </pre>
          </div>
        </motion.div>
      </div>

      {/* Scroll Indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.2 }}
        className="absolute bottom-8 left-1/2 transform -translate-x-1/2"
      >
        <motion.div
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 1.5, repeat: Infinity }}
          className="w-6 h-10 border-2 border-[#2F6DAB] rounded-full flex items-start justify-center p-2"
        >
          <motion.div
            animate={{ y: [0, 12, 0] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="w-1 h-3 bg-[#2F6DAB] rounded-full"
          />
        </motion.div>
      </motion.div>
    </section>
  );
}

