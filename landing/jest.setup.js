import '@testing-library/jest-dom';

// jsdom doesn't implement IntersectionObserver, but framer-motion's
// whileInView animations (used throughout the landing page) require it.
global.IntersectionObserver = class IntersectionObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};
