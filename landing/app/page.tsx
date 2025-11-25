/**
 * Cost Melt Landing - Main Page
 * 
 * Complete landing page with all sections.
 */

import Hero from '../components/Hero';
import FeatureGrid from '../components/FeatureGrid';
import Pricing from '../components/Pricing';
import Testimonial from '../components/Testimonial';
import CTA from '../components/CTA';
import Footer from '../components/Footer';

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-[#0B1221]">
      <Hero />
      <FeatureGrid />
      <Pricing />
      <Testimonial />
      <CTA />
      <Footer />
    </main>
  );
}
