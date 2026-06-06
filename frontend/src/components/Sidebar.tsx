import React, { useState, useEffect } from 'react';
import { m, AnimatePresence } from 'framer-motion';
import { 
  Shield, MessageSquare, Globe, UploadCloud, Workflow, 
  Settings, Home, ChevronLeft, ChevronRight, Sun, Moon,
  LogOut, Activity, Menu, X
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: any) => void;
  apiStatus: 'unchecked' | 'online' | 'offline';
  theme: 'light' | 'dark';
  toggleTheme: () => void;
}

export default function Sidebar({ activeTab, setActiveTab, apiStatus, theme, toggleTheme }: SidebarProps) {
  // Persist collapse state in localStorage
  const [isCollapsed, setIsCollapsed] = useState(() => {
    const saved = localStorage.getItem('bg_sidebar_collapsed');
    return saved === 'true';
  });

  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    localStorage.setItem('bg_sidebar_collapsed', String(isCollapsed));
  }, [isCollapsed]);

  const menuItems = [
    { id: 'detector', label: 'Detektor Teks', icon: MessageSquare, desc: 'Analisis teks real-time' },
    { id: 'social', label: 'Media Sosial (Link)', icon: Globe, desc: 'Scrape komentar & moderasi' },
    { id: 'batch', label: 'Batch Analisis', icon: UploadCloud, desc: 'Analisis dokumen massal' },
    { id: 'active-learning', label: 'Active Learning', icon: Workflow, desc: 'Latih ulang model & moderasi' },
    { id: 'settings', label: 'Pengaturan', icon: Settings, desc: 'Kunci API & sesi scraper' }
  ];

  const sidebarWidth = isCollapsed ? 'w-20' : 'w-64';

  const renderContent = () => (
    <>
      {/* Brand Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-150 dark:border-[#262a45] h-16 shrink-0">
        <div 
          onClick={() => setActiveTab('home')}
          className="flex items-center gap-3 cursor-pointer select-none group"
        >
          <div className="w-9 h-9 rounded-xl bg-blue-50 dark:bg-blue-500/10 flex items-center justify-center text-blue-600 dark:text-blue-400 group-hover:scale-105 transition-transform">
            <Shield className="w-5 h-5 fill-blue-600/10 dark:fill-blue-400/10 text-blue-600 dark:text-blue-400" />
          </div>
          {!isCollapsed && (
            <m.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              className="flex flex-col"
            >
              <span className="font-black text-sm text-gray-900 dark:text-[#faf8ff] tracking-tight group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                BullyGuard ID
              </span>
              <span className="text-[9px] font-bold text-gray-400 uppercase tracking-widest leading-none">
                AI Dashboard
              </span>
            </m.div>
          )}
        </div>

        {/* Desktop Collapse Arrow Button */}
        {!mobileOpen && (
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="hidden md:flex w-6 h-6 rounded-lg border border-gray-200 dark:border-[#262a45] bg-white dark:bg-[#151726] hover:bg-gray-50 dark:hover:bg-white/5 items-center justify-center text-gray-400 hover:text-gray-600 dark:hover:text-[#faf8ff] cursor-pointer transition-colors shadow-xxs"
          >
            {isCollapsed ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronLeft className="w-3.5 h-3.5" />}
          </button>
        )}
      </div>

      {/* Navigation Items */}
      <div 
        data-lenis-prevent
        className="flex-1 overflow-y-auto px-3 py-4 flex flex-col gap-1.5 custom-scrollbar"
      >
        {menuItems.map((item) => {
          const isActive = activeTab === item.id;
          const Icon = item.icon;

          return (
            <button
              key={item.id}
              onClick={() => {
                setActiveTab(item.id);
                setMobileOpen(false);
              }}
              title={isCollapsed ? item.label : undefined}
              className={`relative flex items-center gap-3.5 px-3 py-2.5 rounded-xl border-none cursor-pointer text-left transition-colors group select-none ${
                isActive
                  ? 'text-blue-600 dark:text-blue-400 font-semibold'
                  : 'text-gray-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 bg-transparent'
              }`}
            >
              {isActive && (
                <m.span
                  layoutId="active-sidebar-pill"
                  className="absolute inset-0 bg-blue-50/70 dark:bg-blue-500/10 rounded-xl -z-10"
                  transition={{ type: "spring", stiffness: 380, damping: 30 }}
                />
              )}
              <div className={`shrink-0 transition-transform ${isActive ? 'scale-105' : 'group-hover:scale-105'}`}>
                <Icon className="w-5 h-5" />
              </div>
              
              {!isCollapsed && (
                <m.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex flex-col min-w-0"
                >
                  <span className="text-xs leading-none">{item.label}</span>
                  <span className="text-[9px] text-gray-400 font-normal mt-0.5 leading-none overflow-hidden text-ellipsis whitespace-nowrap">
                    {item.desc}
                  </span>
                </m.div>
              )}
            </button>
          );
        })}
      </div>

      {/* Sidebar Footer Actions */}
      <div className="p-3 border-t border-gray-150 dark:border-[#262a45] flex flex-col gap-2 shrink-0 bg-gray-50/30 dark:bg-black/5">
        {/* Kembali ke Landing Page */}
        <button
          onClick={() => {
            setActiveTab('home');
            setMobileOpen(false);
          }}
          className={`flex items-center gap-3.5 px-3 py-2.5 rounded-xl border-none cursor-pointer text-left text-gray-500 hover:text-rose-600 dark:text-gray-400 dark:hover:text-rose-400 bg-transparent hover:bg-rose-50/50 dark:hover:bg-rose-950/10 transition-colors select-none`}
          title={isCollapsed ? 'Kembali ke Home' : undefined}
        >
          <Home className="w-5 h-5 shrink-0" />
          {!isCollapsed && <span className="text-xs font-medium leading-none">Kembali ke Home</span>}
        </button>

        {/* Theme Toggle & API Status */}
        <div className={`flex ${isCollapsed ? 'flex-col gap-3 items-center justify-center py-2' : 'justify-between items-center px-2 py-1'}`}>
          {/* Theme Switcher Icon */}
          <button
            onClick={toggleTheme}
            className="w-8 h-8 rounded-lg border border-gray-200 dark:border-[#262a45] bg-white dark:bg-[#151726] flex items-center justify-center cursor-pointer text-gray-400 hover:text-gray-600 dark:hover:text-[#faf8ff] transition-colors shadow-xxs"
            title={theme === 'dark' ? 'Mode Terang' : 'Mode Gelap'}
          >
            {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-500" />}
          </button>

          {/* Connection Speed / Indicator */}
          {isCollapsed ? (
            <span 
              className={`w-2.5 h-2.5 rounded-full ${
                apiStatus === 'online' 
                  ? 'bg-emerald-500 animate-pulse' 
                  : apiStatus === 'offline' 
                    ? 'bg-rose-500' 
                    : 'bg-gray-400'
              }`}
              title={apiStatus === 'online' ? 'Connected' : apiStatus === 'offline' ? 'Offline' : 'Checking'}
            />
          ) : (
            <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[9px] font-bold border uppercase tracking-wider ${
              apiStatus === 'online' 
                ? 'bg-emerald-50/50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-100 dark:border-emerald-500/20' 
                : apiStatus === 'offline'
                  ? 'bg-rose-50/50 dark:bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-100 dark:border-rose-500/20'
                  : 'bg-gray-50/50 dark:bg-white/5 text-gray-400 border-gray-250 dark:border-gray-700'
            }`}>
              <span className={`w-1 h-1 rounded-full ${
                apiStatus === 'online' ? 'bg-emerald-500 animate-pulse' : apiStatus === 'offline' ? 'bg-rose-500' : 'bg-gray-400'
              }`} />
              {apiStatus === 'online' ? 'Online' : apiStatus === 'offline' ? 'Offline' : 'Checking'}
            </span>
          )}
        </div>
      </div>
    </>
  );

  return (
    <>
      {/* --- DESKTOP SIDEBAR --- */}
      <aside className={`hidden md:flex flex-col h-screen sticky top-0 z-40 border-r border-gray-150 dark:border-[#262a45] bg-white dark:bg-[#151726] transition-all duration-300 shadow-sm shrink-0 overflow-hidden ${sidebarWidth}`}>
        {renderContent()}
      </aside>

      {/* --- MOBILE TOP NAVIGATION BAR --- */}
      <header className="md:hidden fixed top-0 left-0 w-full h-16 bg-white/95 dark:bg-[#151726]/95 backdrop-blur-md border-b border-gray-150 dark:border-[#262a45] flex items-center justify-between px-4 z-40 shadow-xxs">
        <div className="flex items-center gap-2.5">
          <Shield className="w-5.5 h-5.5 text-blue-600 dark:text-blue-400" />
          <span className="font-black text-sm text-gray-900 dark:text-[#faf8ff] tracking-tight">BullyGuard ID</span>
        </div>
        
        <button
          onClick={() => setMobileOpen(true)}
          className="w-9 h-9 rounded-xl border border-gray-200 dark:border-[#262a45] bg-transparent flex items-center justify-center cursor-pointer text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-[#faf8ff] transition-colors"
          aria-label="Open menu"
        >
          <Menu className="w-5 h-5" />
        </button>
      </header>

      {/* Space occupier to offset fixed header on mobile */}
      <div className="md:hidden h-16 w-full shrink-0" />

      {/* --- MOBILE DRAWER OVERLAY & SIDEBAR PANEL --- */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            {/* Backdrop transparent blur */}
            <m.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileOpen(false)}
              className="md:hidden fixed inset-0 bg-black/30 dark:bg-black/50 backdrop-blur-sm z-45"
            />

            {/* Slide-in sidebar drawer panel */}
            <m.aside
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 220 }}
              className="md:hidden fixed top-0 left-0 h-screen w-64 bg-white dark:bg-[#151726] border-r border-gray-150 dark:border-[#262a45] z-50 flex flex-col shadow-2xl overflow-hidden"
            >
              {/* Close Drawer Button */}
              <div className="absolute top-3.5 right-3.5 z-50">
                <button
                  onClick={() => setMobileOpen(false)}
                  className="w-7 h-7 rounded-lg border border-gray-200 dark:border-[#262a45] bg-white dark:bg-[#151726] flex items-center justify-center cursor-pointer text-gray-400 hover:text-gray-600 dark:hover:text-[#faf8ff] transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {renderContent()}
            </m.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
