/**
 * Cost Melt Dashboard - Topbar Component
 * 
 * Top navigation bar.
 */

'use client';

import { Bell, Settings, User } from 'lucide-react';

export default function Topbar() {
  return (
    <div className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">Dashboard</h2>
      </div>
      
      <div className="flex items-center gap-4">
        <button className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors">
          <Bell className="w-5 h-5" />
        </button>
        <button className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors">
          <Settings className="w-5 h-5" />
        </button>
        <button className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors">
          <User className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}

