/**
 * Cost Melt Landing - Footer Component
 * 
 * Footer with links and copyright.
 */

'use client';

import Link from 'next/link';
import { Twitter, Github } from 'lucide-react';

const footerLinks = {
  product: [
    { href: '/pricing', label: 'Pricing' },
    { href: '#docs', label: 'Docs' },
    { href: '#dashboard', label: 'Dashboard' },
  ],
  legal: [
    { href: '/privacy', label: 'Privacy Policy' },
    { href: '/terms', label: 'Terms' },
  ],
  social: [
    { href: '#twitter', label: 'Twitter', icon: Twitter },
    { href: '#github', label: 'GitHub', icon: Github },
  ],
};

export default function Footer() {
  return (
    <footer className="bg-[#0B1221] border-t border-[#2F6DAB]/20">
      <div className="container mx-auto px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand */}
          <div>
            <Link href="/" className="flex items-center space-x-2 mb-4">
              <div className="w-8 h-8 bg-gradient-to-br from-[#2F6DAB] to-[#1C3F70] rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">CM</span>
              </div>
              <span className="text-white font-bold text-xl">Cost Melt</span>
            </Link>
            <p className="text-gray-400 text-sm">
              Melt your AI costs by 40-70% automatically.
            </p>
          </div>

          {/* Product Links */}
          <div>
            <h3 className="text-white font-semibold mb-4">Product</h3>
            <ul className="space-y-2">
              {footerLinks.product.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-gray-400 hover:text-white transition-colors text-sm"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal Links */}
          <div>
            <h3 className="text-white font-semibold mb-4">Legal</h3>
            <ul className="space-y-2">
              {footerLinks.legal.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-gray-400 hover:text-white transition-colors text-sm"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Social Links */}
          <div>
            <h3 className="text-white font-semibold mb-4">Connect</h3>
            <ul className="space-y-2">
              {footerLinks.social.map((link) => {
                const Icon = link.icon;
                return (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="text-gray-400 hover:text-white transition-colors text-sm flex items-center gap-2"
                    >
                      <Icon className="w-4 h-4" />
                      {link.label}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        </div>

        {/* Copyright */}
        <div className="border-t border-[#2F6DAB]/20 pt-8 text-center">
          <p className="text-gray-400 text-sm">
            © 2025 Cost Melt. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}

