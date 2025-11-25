/**
 * Cost Melt Landing - Pricing Component
 * 
 * 3-tier SaaS pricing with modern cards.
 */

'use client';

import { motion } from 'framer-motion';
import { Check, ArrowRight } from 'lucide-react';
import Link from 'next/link';
import Section from './Section';

const plans = [
  {
    name: 'Free',
    price: '$0',
    period: '/month',
    description: 'Perfect for getting started',
    features: [
      '5k optimized requests/month',
      'Basic routing',
      'Limited caching',
      'Community support',
    ],
    cta: 'Get Started',
    href: '#start-free',
    popular: false,
    gradient: 'from-gray-700 to-gray-800',
  },
  {
    name: 'Pro',
    price: '$49',
    period: '/month',
    description: 'For growing teams',
    features: [
      '250k optimized requests',
      'Semantic caching',
      'Prompt compression',
      'Micro-batching',
      'Cost analytics',
      'Email support',
    ],
    cta: 'Start Pro',
    href: '#start-pro',
    popular: true,
    gradient: 'from-[#2F6DAB] to-[#1C3F70]',
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: '',
    description: 'For large organizations',
    features: [
      'Unlimited requests',
      'VPC deployment',
      'Custom routing rules',
      'SOC2 / data privacy support',
      'Dedicated engineer',
    ],
    cta: 'Contact Sales',
    href: '#contact-sales',
    popular: false,
    gradient: 'from-[#1C3F70] to-[#0B1221]',
  },
];

export default function Pricing() {
  return (
    <Section id="pricing" className="bg-gradient-to-b from-[#0B1221] to-[#1a2332]">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
        className="text-center mb-16"
      >
        <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
          Simple, Transparent Pricing
        </h2>
        <p className="text-xl text-gray-400 max-w-2xl mx-auto">
          Choose the plan that fits your needs. All plans include our core optimization features.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
        {plans.map((plan, index) => (
          <motion.div
            key={plan.name}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
            whileHover={{ y: -8, scale: 1.02 }}
            className={`relative bg-[#1a2332] border rounded-2xl p-8 ${
              plan.popular
                ? 'border-[#2F6DAB] shadow-2xl shadow-[#2F6DAB]/20 scale-105'
                : 'border-[#2F6DAB]/20'
            }`}
          >
            {plan.popular && (
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                <span className="bg-gradient-to-r from-[#2F6DAB] to-[#1C3F70] text-white px-4 py-1 rounded-full text-sm font-semibold">
                  Most Popular
                </span>
              </div>
            )}

            <div className="mb-8">
              <h3 className="text-2xl font-bold text-white mb-2">{plan.name}</h3>
              <p className="text-gray-400 text-sm mb-4">{plan.description}</p>
              <div className="flex items-baseline">
                <span className="text-5xl font-bold text-white">{plan.price}</span>
                {plan.period && (
                  <span className="text-gray-400 ml-2">{plan.period}</span>
                )}
              </div>
            </div>

            <ul className="space-y-4 mb-8">
              {plan.features.map((feature, featureIndex) => (
                <li key={featureIndex} className="flex items-start">
                  <Check className="w-5 h-5 text-[#00E0FF] mr-3 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-300">{feature}</span>
                </li>
              ))}
            </ul>

            <Link
              href={plan.href}
              className={`block w-full py-3 px-6 rounded-lg font-semibold text-center transition-all ${
                plan.popular
                  ? 'bg-gradient-to-r from-[#2F6DAB] to-[#1C3F70] text-white hover:opacity-90'
                  : 'bg-[#0B1221] border-2 border-[#2F6DAB] text-white hover:bg-[#2F6DAB]/10'
              }`}
            >
              {plan.cta}
            </Link>
          </motion.div>
        ))}
      </div>
    </Section>
  );
}

