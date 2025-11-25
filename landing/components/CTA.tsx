/**
 * Cost Melt Landing - CTA Component
 * 
 * Bold call-to-action section with gradient background.
 */

'use client';

import { motion } from 'framer-motion';
import { ArrowRight, Calendar } from 'lucide-react';
import Link from 'next/link';
import Section from './Section';

export default function CTA() {
  return (
    <Section className="relative overflow-hidden">
      {/* Gradient Background */}
      <div className="absolute inset-0 bg-gradient-to-r from-[#2F6DAB] via-[#1C3F70] to-[#2F6DAB] opacity-90" />
      <div className="absolute inset-0 bg-[#0B1221]/50" />

      {/* Animated Background Elements */}
      <motion.div
        className="absolute top-0 left-1/4 w-96 h-96 bg-[#00E0FF] rounded-full blur-3xl opacity-20"
        animate={{
          x: [0, 100, 0],
          y: [0, -50, 0],
          scale: [1, 1.2, 1],
        }}
        transition={{
          duration: 15,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />

      <div className="relative z-10 text-center">
        <motion.h2
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="text-4xl md:text-6xl font-bold text-white mb-6"
        >
          Start cutting your AI costs today.
        </motion.h2>
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-xl text-gray-200 mb-12 max-w-2xl mx-auto"
        >
          Join thousands of developers saving 40-70% on their LLM costs
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <Link
            href="#start-free"
            className="group px-8 py-4 bg-white text-[#2F6DAB] rounded-lg font-semibold text-lg hover:bg-gray-100 transition-colors flex items-center gap-2 shadow-lg"
          >
            Start Free
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
          <Link
            href="#book-demo"
            className="px-8 py-4 bg-transparent border-2 border-white text-white rounded-lg font-semibold text-lg hover:bg-white/10 transition-colors flex items-center gap-2"
          >
            <Calendar className="w-5 h-5" />
            Book a Demo
          </Link>
        </motion.div>
      </div>
    </Section>
  );
}

