/**
 * Cost Melt Landing - Terms of Service Page
 */

import Footer from '../../components/Footer';
import Section from '../../components/Section';

export default function TermsPage() {
  return (
    <main className="min-h-screen bg-[#0B1221] pt-20">
      <Section>
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-8">
            Terms of Service
          </h1>
          <div className="prose prose-invert max-w-none">
            <p className="text-gray-300 text-lg mb-6">
              <strong>Last Updated:</strong> January 2025
            </p>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-white mb-4">1. Acceptance of Terms</h2>
              <p className="text-gray-300 mb-4">
                By accessing and using Cost Melt, you accept and agree to be bound by these Terms of Service.
                If you do not agree, you may not use our service.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-white mb-4">2. Service Description</h2>
              <p className="text-gray-300 mb-4">
                Cost Melt provides an LLM proxy service that optimizes API costs through routing, caching,
                batching, and compression. We reserve the right to modify or discontinue the service at any time.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-white mb-4">3. User Accounts</h2>
              <p className="text-gray-300 mb-4">
                You are responsible for:
              </p>
              <ul className="text-gray-300 list-disc list-inside space-y-2 mb-4">
                <li>Maintaining the security of your account credentials</li>
                <li>All activities that occur under your account</li>
                <li>Providing accurate and current information</li>
                <li>Notifying us immediately of unauthorized access</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-white mb-4">4. Acceptable Use</h2>
              <p className="text-gray-300 mb-4">
                You agree not to:
              </p>
              <ul className="text-gray-300 list-disc list-inside space-y-2 mb-4">
                <li>Use the service for illegal purposes</li>
                <li>Attempt to reverse engineer or compromise the service</li>
                <li>Exceed your plan's usage limits without authorization</li>
                <li>Interfere with or disrupt the service</li>
                <li>Share API keys or credentials with unauthorized parties</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-white mb-4">5. Payment and Billing</h2>
              <p className="text-gray-300 mb-4">
                Subscription fees are billed in advance. You agree to:
              </p>
              <ul className="text-gray-300 list-disc list-inside space-y-2 mb-4">
                <li>Pay all fees associated with your plan</li>
                <li>Provide valid payment information</li>
                <li>Understand that fees are non-refundable except as required by law</li>
                <li>Accept that prices may change with 30 days notice</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-white mb-4">6. Intellectual Property</h2>
              <p className="text-gray-300 mb-4">
                All content, features, and functionality of Cost Melt are owned by us and protected by
                intellectual property laws. You may not copy, modify, or distribute our service without permission.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-white mb-4">7. Limitation of Liability</h2>
              <p className="text-gray-300 mb-4">
                Cost Melt is provided "as is" without warranties. We are not liable for:
              </p>
              <ul className="text-gray-300 list-disc list-inside space-y-2 mb-4">
                <li>Indirect, incidental, or consequential damages</li>
                <li>Loss of data or profits</li>
                <li>Service interruptions or downtime</li>
                <li>Third-party provider issues</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-white mb-4">8. Termination</h2>
              <p className="text-gray-300 mb-4">
                Either party may terminate service at any time. Upon termination:
              </p>
              <ul className="text-gray-300 list-disc list-inside space-y-2 mb-4">
                <li>Your access will be immediately revoked</li>
                <li>Outstanding fees remain due</li>
                <li>Data may be deleted after 30 days</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-white mb-4">9. Changes to Terms</h2>
              <p className="text-gray-300 mb-4">
                We reserve the right to modify these terms. Continued use after changes constitutes acceptance.
                We will notify users of material changes via email.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-white mb-4">10. Contact Information</h2>
              <p className="text-gray-300 mb-4">
                For questions about these terms, contact us at:
              </p>
              <p className="text-gray-300">
                <strong>Email:</strong> legal@costmelt.com
              </p>
            </section>
          </div>
        </div>
      </Section>
      <Footer />
    </main>
  );
}

