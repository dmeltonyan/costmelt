import './globals.css'
import Sidebar from '../components/Sidebar'
import Topbar from '../components/Topbar'

export const metadata = {
  title: 'Cost Melt Dashboard',
  description: 'LLM Cost Optimization Dashboard',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        <div className="grid grid-cols-[240px_1fr] h-screen">
          <Sidebar />
          <div className="flex flex-col overflow-hidden">
            <Topbar />
            <main className="flex-1 overflow-y-auto bg-gray-50">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  )
}
