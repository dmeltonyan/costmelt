/**
 * Cost Melt Landing - Page Tests
 * 
 * Tests for landing pages and components.
 */

import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

// Mock Next.js router
jest.mock('next/navigation', () => ({
  usePathname: () => '/',
}));

describe('Landing Pages', () => {
  describe('Home Page', () => {
    it('renders hero section', async () => {
      const LandingPage = (await import('../app/page')).default;
      render(<LandingPage />);
      
      // Check for hero text
      expect(screen.getByText(/Melt Your AI Costs/i)).toBeInTheDocument();
    });

    it('renders feature grid', async () => {
      const LandingPage = (await import('../app/page')).default;
      render(<LandingPage />);

      // "Semantic Caching" also appears in the pricing plan feature lists
      // further down the page, so a plain text match is ambiguous — target
      // the feature grid's heading elements directly.
      expect(screen.getByRole('heading', { name: /Smart Model Routing/i })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: /Semantic Caching/i })).toBeInTheDocument();
    });

    it('renders pricing section', async () => {
      const LandingPage = (await import('../app/page')).default;
      render(<LandingPage />);

      // "Pricing" alone also matches the footer's nav link — the section
      // heading's full text is unambiguous.
      expect(screen.getByText(/Simple, Transparent Pricing/i)).toBeInTheDocument();
    });

    it('renders testimonials', async () => {
      const LandingPage = (await import('../app/page')).default;
      render(<LandingPage />);
      
      expect(screen.getByText(/Loved by Developers/i)).toBeInTheDocument();
    });

    it('renders footer', async () => {
      const LandingPage = (await import('../app/page')).default;
      render(<LandingPage />);
      
      expect(screen.getByText(/© 2025 Cost Melt/i)).toBeInTheDocument();
    });
  });

  describe('Pricing Page', () => {
    it('renders pricing plans', async () => {
      const PricingPage = (await import('../app/pricing/page')).default;
      render(<PricingPage />);

      // "Pricing" alone also matches the footer's nav link, and "Pro" also
      // matches substrings like "Prompt compression" and the "Start Pro"
      // CTA button — target each plan's heading directly.
      expect(screen.getByText(/Simple, Transparent Pricing/i)).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Free' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Pro' })).toBeInTheDocument();
    });
  });

  describe('Privacy Page', () => {
    it('renders privacy policy', async () => {
      const PrivacyPage = (await import('../app/privacy/page')).default;
      render(<PrivacyPage />);

      // The page's <h1> and its footer nav link both say "Privacy Policy",
      // so a plain text match is ambiguous — target the heading directly.
      expect(screen.getByRole('heading', { name: /Privacy Policy/i, level: 1 })).toBeInTheDocument();
    });
  });

  describe('Terms Page', () => {
    it('renders terms of service', async () => {
      const TermsPage = (await import('../app/terms/page')).default;
      render(<TermsPage />);

      // The page's <h1> and its own body copy both say "Terms of Service",
      // so a plain text match is ambiguous — target the heading directly.
      expect(screen.getByRole('heading', { name: /Terms of Service/i, level: 1 })).toBeInTheDocument();
    });
  });
});

