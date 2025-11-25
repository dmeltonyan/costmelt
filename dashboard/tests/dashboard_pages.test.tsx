/**
 * Cost Melt Dashboard - Page Tests
 * 
 * Tests for dashboard pages and components.
 */

import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

// Mock API functions
jest.mock('../lib/api', () => ({
  getStats: jest.fn(() => Promise.resolve({
    total_requests: 1000,
    total_tokens_in: 50000,
    total_tokens_out: 25000,
    total_actual_cost: 10.5,
    total_baseline_cost: 30.0,
    total_savings: 19.5,
    savings_pct: 65.0,
    cache_hit_rate: 45.0
  })),
  getUsage: jest.fn(() => Promise.resolve({
    models: [
      { model: 'gpt-4o-mini', count: 500, input_tokens: 25000, output_tokens: 12500, actual_cost: 5.0 }
    ]
  })),
  getCache: jest.fn(() => Promise.resolve({
    cache_hits: 450,
    cache_misses: 550,
    hit_rate: 45.0,
    recent_hits: []
  })),
  getRouting: jest.fn(() => Promise.resolve({
    complexity_distribution: { '0': 300, '1': 500, '2': 200 },
    model_distribution: { 'gpt-4o-mini': 500, 'gpt-4o': 200 }
  })),
  getDaily: jest.fn(() => Promise.resolve({
    days: [
      { date: '2025-01-01', requests: 100, tokens_in: 5000, tokens_out: 2500, actual_cost: 1.0, baseline_cost: 3.0, savings: 2.0 }
    ]
  })),
  getModels: jest.fn(() => Promise.resolve({
    entries: [
      { model: 'gpt-4o-mini', requests: 500, actual_cost: 5.0, baseline_cost: 15.0, savings_pct: 66.7 }
    ]
  })),
  getSavings: jest.fn(() => Promise.resolve({
    savings_over_time: [
      { date: '2025-01-01', saved: 2.0 }
    ]
  }))
}));

describe('Dashboard Pages', () => {
  beforeEach(() => {
    // Mock window.location
    Object.defineProperty(window, 'location', {
      value: {
        reload: jest.fn()
      },
      writable: true
    });
  });

  describe('Home Page', () => {
    it('renders without crashing', async () => {
      const DashboardPage = (await import('../app/page')).default;
      render(<DashboardPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Dashboard Overview')).toBeInTheDocument();
      });
    });

    it('displays stats cards', async () => {
      const DashboardPage = (await import('../app/page')).default;
      render(<DashboardPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Total Requests')).toBeInTheDocument();
        expect(screen.getByText('Cost Saved')).toBeInTheDocument();
      });
    });
  });

  describe('Usage Page', () => {
    it('renders without crashing', async () => {
      const UsagePage = (await import('../app/usage/page')).default;
      render(<UsagePage />);
      
      await waitFor(() => {
        expect(screen.getByText('Usage by Model')).toBeInTheDocument();
      });
    });

    it('displays model usage table', async () => {
      const UsagePage = (await import('../app/usage/page')).default;
      render(<UsagePage />);
      
      await waitFor(() => {
        expect(screen.getByText('Model Usage Table')).toBeInTheDocument();
      });
    });
  });

  describe('Cache Page', () => {
    it('renders without crashing', async () => {
      const CachePage = (await import('../app/cache/page')).default;
      render(<CachePage />);
      
      await waitFor(() => {
        expect(screen.getByText('Cache Performance')).toBeInTheDocument();
      });
    });

    it('displays cache metrics', async () => {
      const CachePage = (await import('../app/cache/page')).default;
      render(<CachePage />);
      
      await waitFor(() => {
        expect(screen.getByText('Cache Hits')).toBeInTheDocument();
        expect(screen.getByText('Hit Rate')).toBeInTheDocument();
      });
    });
  });

  describe('Routing Page', () => {
    it('renders without crashing', async () => {
      const RoutingPage = (await import('../app/routing/page')).default;
      render(<RoutingPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Routing Breakdown')).toBeInTheDocument();
      });
    });
  });

  describe('Models Page', () => {
    it('renders without crashing', async () => {
      const ModelsPage = (await import('../app/models/page')).default;
      render(<ModelsPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Model Comparison')).toBeInTheDocument();
      });
    });
  });

  describe('Daily Page', () => {
    it('renders without crashing', async () => {
      const DailyPage = (await import('../app/daily/page')).default;
      render(<DailyPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Daily Usage')).toBeInTheDocument();
      });
    });
  });

  describe('Savings Page', () => {
    it('renders without crashing', async () => {
      const SavingsPage = (await import('../app/savings/page')).default;
      render(<SavingsPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Savings Analysis')).toBeInTheDocument();
      });
    });
  });
});

