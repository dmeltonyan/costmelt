import './globals.css'
import Navbar from '../components/Navbar'

export const metadata = {
  title: 'Cost Melt - Melt Your AI Costs by 40-70%',
  description: 'The smartest LLM router, cache, and optimizer that cuts your token bills without changing your code.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        <Navbar />
        {children}
      </body>
    </html>
  )
}
