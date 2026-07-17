/**
 * Cost Melt Landing - Testimonial Component
 * 
 * Customer testimonials with avatars and stars.
 */

'use client';

import { motion } from 'framer-motion';
import { Star } from 'lucide-react';
import Section from './Section';

const testimonials = [
  {
    name: 'Alex Chen',
    role: 'Indie AI Founder',
    company: 'AI Startup',
    avatar: 'AC',
    quote: 'Cost Melt instantly shaved 62% off our OpenAI bill. Plug-and-play magic.',
    rating: 5,
  },
  {
    name: 'Sarah Johnson',
    role: 'SaaS CTO',
    company: 'Tech Corp',
    avatar: 'SJ',
    quote: "We didn't have to rewrite anything — it just works.",
    rating: 5,
  },
  {
    name: 'Michael Park',
    role: 'ML Engineer',
    company: 'Data Labs',
    avatar: 'MP',
    quote: 'The dashboard tells us exactly where our models burn money. Essential.',
    rating: 5,
  },
];

export default function Testimonial() {
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
          Loved by Developers
        </h2>
        <p className="text-xl text-gray-400 max-w-2xl mx-auto">
          See what our users are saying about Cost Melt
        </p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
        {testimonials.map((testimonial, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
            whileHover={{ y: -8, scale: 1.02 }}
            className="bg-[#1a2332] border border-[#2F6DAB]/20 rounded-xl p-8 hover:border-[#2F6DAB]/50 transition-all duration-300"
          >
            {/* Stars */}
            <div className="flex gap-1 mb-4">
              {Array.from({ length: testimonial.rating }).map((_, i) => (
                <Star
                  key={i}
                  className="w-5 h-5 fill-[#00E0FF] text-[#00E0FF]"
                />
              ))}
            </div>

            {/* Quote */}
            <p className="text-gray-300 text-lg mb-6 leading-relaxed">
              "{testimonial.quote}"
            </p>

            {/* Author */}
            <div className="flex items-center">
              <div className="w-12 h-12 bg-gradient-to-br from-[#2F6DAB] to-[#1C3F70] rounded-full flex items-center justify-center text-white font-bold mr-4">
                {testimonial.avatar}
              </div>
              <div>
                <div className="text-white font-semibold">{testimonial.name}</div>
                <div className="text-gray-400 text-sm">
                  {testimonial.role} at {testimonial.company}
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </Section>
  );
}

