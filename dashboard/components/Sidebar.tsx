/**
 * Cost Melt Dashboard - Sidebar Component
 * 
 * Navigation sidebar with menu links.
 */

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Activity,
  Database,
  Route,
  Cpu,
  Calendar,
  TrendingUp,
  Menu
} from 'lucide-react';
import { cn } from '../lib/utils';

const menuItems = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/usage', label: 'Usage', icon: Activity },
  { href: '/cache', label: 'Cache', icon: Database },
  { href: '/routing', label: 'Routing', icon: Route },
  { href: '/models', label: 'Models', icon: Cpu },
  { href: '/daily', label: 'Daily', icon: Calendar },
  { href: '/savings', label: 'Savings', icon: TrendingUp },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="h-screen w-60 bg-gray-900 text-white flex flex-col">
      {/* Logo/Brand */}
      <div className="p-6 border-b border-gray-800">
        <h1 className="text-xl font-bold">Cost Melt</h1>
        <p className="text-sm text-gray-400">Cost Optimization</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-4 py-3 rounded-lg transition-colors",
                isActive
                  ? "bg-blue-600 text-white"
                  : "text-gray-300 hover:bg-gray-800 hover:text-white"
              )}
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-800">
        <p className="text-xs text-gray-400">Cost Melt v1.0</p>
      </div>
    </div>
  );
}

