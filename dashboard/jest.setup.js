import '@testing-library/jest-dom';

// jsdom doesn't implement ResizeObserver, but recharts' ResponsiveContainer
// (used throughout the dashboard's chart components) requires it.
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};
