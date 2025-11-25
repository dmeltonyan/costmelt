/**
 * Cost Melt Landing - Privacy Policy Page
 */

import Footer from '../../components/Footer';
import Section from '../../components/Section';

export default function PrivacyPage() {
  return (
    <main className="min-h-screen bg-[#0B1221] pt-20">
      <Section>
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-8">
            Privacy Policy
          </h1>
          <div className="prose prose-invert max-w-none">
            <p className="text-gray-300 text-lg mb-6">
              <strong>Last Updated:</strong> January 2025
            </p>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-white mb-4">1. Information We Collect</h2>
              <p className="text-gray-300 mb-4">
                Cost Melt collects information necessary to provide our service, including:
              </p>
              <ul className="text-gray-300 list-disc list-inside space-y-2 mb-4">
                <li>Account information (email, name, company)</li>
                <li>API usage data and request logs</li>
                <li>Payment information (processed securely through third-party providers)</li>
                <li>Technical data (IP addresses, browser type, device information)</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-white mb-4">2. How We Use Your Information</h2>
              <p className="text-gray-300 mb-4">
                We use collected information to:
              </p>
              <ul className="text-gray-300 list-disc list-inside space-y-2 mb-4">
                <li>Provide and improve our services</li>
                <li>Process payments and manage subscriptions</li>
                <li>Send service-related communications</li>
                <li>Analyze usage patterns to optimize performance</li>
                <li>Comply with legal obligations</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-white mb-4">3. Data Security</h2>
              <p className="text-gray-300 mb-4">
                We implement industry-standard security measures to protect your data:
              </p>
              <ul className="text-gray-300 list-disc list-inside space-y-2 mb-4">
                <li>Encryption in transit and at rest</li>
                <li>Secure API key storage</li>
                <li>Regular security audits</li>
                <li>Access controls and authentication</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-white mb-4">4. Data Sharing</h2>
              <p className="text-gray-300 mb-4">
                We do not sell your data. We may share information only:
              </p>
              <ul className="text-gray-300 list-disc list-inside space-y-2 mb-4">
                <li>With service providers who assist in operations</li>
                <li>When required by law or legal process</li>
                <li>To protect our rights and prevent fraud</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-white mb-4">5. Your Rights</h2>
              <p className="text-gray-300 mb-4">
                You have the right to:
              </p>
              <ul className="text-gray-300 list-disc list-inside space-y-2 mb-4">
                <li>Access your personal data</li>
                <li>Correct inaccurate information</li>
                <li>Delete your account and data</li>
                <li>Opt-out of marketing communications</li>
                <li>Export your data</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-bold text-white mb-4">6. Contact Us</h2>
              <p className="text-gray-300 mb-4">
                For privacy-related questions, contact us at:
              </p>
              <p className="text-gray-300">
                <strong>Email:</strong> privacy@costmelt.com
              </p>
            </section>
          </div>
        </div>
      </Section>
      <Footer />
    </main>
  );
}

