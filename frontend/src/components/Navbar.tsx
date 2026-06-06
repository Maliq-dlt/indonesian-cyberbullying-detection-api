import React, { useState } from 'react';
import { Shield, Sun, Moon, Menu, X as XIcon } from 'lucide-react';
import { AnimatePresence, m } from 'framer-motion';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: any) => void;
  apiStatus: 'unchecked' | 'online' | 'offline';
  theme: 'light' | 'dark';
  toggleTheme: () => void;
}

export default function Navbar({ activeTab, setActiveTab, apiStatus, theme, toggleTheme }: NavbarProps) {
  const [mobileOpen, setMobileOpen] = useState(false);

  const tabs = [
    { id: 'home', label: 'Home' },
    { id: 'detector', label: 'Detektor' },
    { id: 'social', label: 'Media Sosial (Link)' },
    { id: 'batch', label: 'Batch Analisis' },
    { id: 'active-learning', label: 'Active Learning' },
    { id: 'settings', label: 'Pengaturan' }
  ];

  return (
    <nav className="fixed top-0 w-full z-50 bg-white/80 dark:bg-[#131314]/80 backdrop-blur-xl border-b border-gray-100 dark:border-gray-850 shadow-sm transition-all duration-300">
      <div className="flex justify-between items-center px-6 py-4 max-w-7xl mx-auto">
        {/* Brand */}
        <button 
          onClick={() => {
            setActiveTab('home');
            setMobileOpen(false);
          }}
          className="font-bold text-xl text-blue-600 dark:text-blue-400 flex items-center gap-2 transition-transform active:scale-95 border-none bg-transparent cursor-pointer"
        >
          <Shield className="w-6 h-6 text-blue-600 dark:text-blue-400 fill-blue-600/10 dark:fill-blue-400/10" />
          BullyGuard ID
        </button>

        {/* Navigation Links (Desktop) */}
        <div className="hidden md:flex items-center gap-1 relative">
          {tabs.map(tab => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`relative px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-300 border-none cursor-pointer bg-transparent z-10 ${
                  isActive
                    ? "text-blue-600 dark:text-blue-400 font-semibold"
                    : "text-gray-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
                }`}
              >
                {tab.label}
                {isActive && (
                  <m.span
                    layoutId="active-nav-pill"
                    className="absolute inset-0 bg-blue-50/75 dark:bg-blue-500/10 rounded-lg -z-10"
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                  />
                )}
              </button>
            );
          })}
        </div>

        {/* Trailing Actions / Status */}
        <div className="flex items-center gap-3">
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${
            apiStatus === 'online' 
              ? "bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-500/20" 
              : apiStatus === 'offline'
                ? "bg-rose-50 dark:bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-200 dark:border-rose-500/20"
                : "bg-gray-50 dark:bg-white/5 text-gray-500 dark:text-gray-400 border-gray-200 dark:border-gray-700"
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${
              apiStatus === 'online' 
                ? "bg-emerald-500 animate-pulse" 
                : apiStatus === 'offline' 
                  ? "bg-rose-500" 
                  : "bg-gray-400"
            }`} />
            {apiStatus === 'online' ? 'Connected' : apiStatus === 'offline' ? 'Offline' : 'Checking'}
          </span>

          {/* Dark Mode Toggle */}
          <button
            onClick={toggleTheme}
            aria-label={theme === 'dark' ? 'Aktifkan Light Mode' : 'Aktifkan Dark Mode'}
            className="relative w-9 h-9 rounded-xl border border-gray-200 dark:border-gray-700 flex items-center justify-center cursor-pointer bg-transparent hover:bg-gray-100 dark:hover:bg-white/10 transition-all duration-300 overflow-hidden"
          >
            <span
              className="absolute inset-0 flex items-center justify-center transition-all duration-400"
              style={{
                opacity: theme === 'dark' ? 1 : 0,
                transform: theme === 'dark' ? 'rotate(0deg) scale(1)' : 'rotate(-90deg) scale(0.5)',
                transition: 'opacity 0.4s cubic-bezier(0.4,0,0.2,1), transform 0.4s cubic-bezier(0.4,0,0.2,1)',
              }}
            >
              <Sun className="w-4.5 h-4.5 text-amber-400" />
            </span>
            <span
              className="absolute inset-0 flex items-center justify-center transition-all duration-400"
              style={{
                opacity: theme === 'light' ? 1 : 0,
                transform: theme === 'light' ? 'rotate(0deg) scale(1)' : 'rotate(90deg) scale(0.5)',
                transition: 'opacity 0.4s cubic-bezier(0.4,0,0.2,1), transform 0.4s cubic-bezier(0.4,0,0.2,1)',
              }}
            >
              <Moon className="w-4.5 h-4.5 text-indigo-500" />
            </span>
          </button>

          {/* Mobile Hamburger Menu Button */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden w-9 h-9 rounded-xl border border-gray-200 dark:border-gray-700 flex items-center justify-center cursor-pointer bg-transparent hover:bg-gray-100 dark:hover:bg-white/10 transition-all"
            aria-label="Toggle menu"
          >
            {mobileOpen ? <XIcon className="w-5 h-5 text-gray-600 dark:text-gray-400" /> : <Menu className="w-5 h-5 text-gray-600 dark:text-gray-400" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Navigation Menu */}
      <AnimatePresence>
        {mobileOpen && (
          <m.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25, ease: 'easeInOut' }}
            className="md:hidden border-t border-gray-100 dark:border-gray-800 bg-white/95 dark:bg-[#131314]/95 backdrop-blur-xl overflow-hidden"
          >
            <div className="flex flex-col px-6 py-4 gap-2">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => {
                    setActiveTab(tab.id);
                    setMobileOpen(false);
                  }}
                  className={`w-full text-left px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 border-none cursor-pointer bg-transparent ${
                    activeTab === tab.id
                      ? "text-blue-600 dark:text-blue-400 bg-blue-50/70 dark:bg-blue-900/20 font-semibold"
                      : "text-gray-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-gray-50 dark:hover:bg-white/5"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </m.div>
        )}
      </AnimatePresence>
    </nav>
  );
}



