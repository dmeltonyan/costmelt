/**
 * Cost Melt Landing - Navbar Component
 * 
 * Sticky navigation bar with logo and links.
 */

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState, useEffect } from 'react';
import { Menu, X } from 'lucide-react';
import { cn } from '../lib/utils';

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { href: '/pricing', label: 'Pricing' },
    { href: '#docs', label: 'Docs' },
    { href: '#login', label: 'Login' },
  ];

  return (
    <nav
      className={cn(
        'fixed top-0 left-0 right-0 z-50 transition-all duration-300',
        scrolled
          ? 'bg-[#0B1221]/80 backdrop-blur-md border-b border-[#2F6DAB]/20'
          : 'bg-transparent'
      )}
    >
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-br from-[#2F6DAB] to-[#1C3F70] rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">CM</span>
            </div>
            <span className="text-white font-bold text-xl">Cost Melt</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-gray-300 hover:text-white transition-colors"
              >
                {link.label}
              </Link>
            ))}
            <Link
              href="#start-free"
              className="px-6 py-2 bg-gradient-to-r from-[#2F6DAB] to-[#1C3F70] text-white rounded-lg font-semibold hover:opacity-90 transition-opacity"
            >
              Start Free
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden text-white"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden mt-4 pb-4 space-y-4">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="block text-gray-300 hover:text-white transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                {link.label}
              </Link>
            ))}
            <Link
              href="#start-free"
              className="block px-6 py-2 bg-gradient-to-r from-[#2F6DAB] to-[#1C3F70] text-white rounded-lg font-semibold text-center"
              onClick={() => setMobileMenuOpen(false)}
            >
              Start Free
            </Link>
          </div>
        )}
      </div>
    </nav>
  );
}

