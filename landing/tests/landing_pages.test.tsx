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
      
      // Check for feature titles
      expect(screen.getByText(/Smart Model Routing/i)).toBeInTheDocument();
      expect(screen.getByText(/Semantic Caching/i)).toBeInTheDocument();
    });

    it('renders pricing section', async () => {
      const LandingPage = (await import('../app/page')).default;
      render(<LandingPage />);
      
      expect(screen.getByText(/Pricing/i)).toBeInTheDocument();
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
      
      expect(screen.getByText(/Pricing/i)).toBeInTheDocument();
      expect(screen.getByText(/Free/i)).toBeInTheDocument();
      expect(screen.getByText(/Pro/i)).toBeInTheDocument();
    });
  });

  describe('Privacy Page', () => {
    it('renders privacy policy', async () => {
      const PrivacyPage = (await import('../app/privacy/page')).default;
      render(<PrivacyPage />);
      
      expect(screen.getByText(/Privacy Policy/i)).toBeInTheDocument();
    });
  });

  describe('Terms Page', () => {
    it('renders terms of service', async () => {
      const TermsPage = (await import('../app/terms/page')).default;
      render(<TermsPage />);
      
      expect(screen.getByText(/Terms of Service/i)).toBeInTheDocument();
    });
  });
});

