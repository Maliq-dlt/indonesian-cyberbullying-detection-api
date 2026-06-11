import React, { useState, useEffect, useCallback, useRef } from 'react';
import { AnimatePresence, useReducedMotion, MotionConfig, LazyMotion, domAnimation } from 'framer-motion';
import { Toaster, toast } from 'sonner';


import Sidebar from './components/Sidebar';
import Home from './components/Home';
import Detector from './components/Detector';
import SocialScraper from './components/SocialScraper';
import BatchAnalysis from './components/BatchAnalysis';
import ActiveLearning from './components/ActiveLearning';
import Settings from './components/Settings';

export default function App() {
  const shouldReduceMotion = useReducedMotion();
  const [activeTab, setActiveTab] = useState<'home' | 'detector' | 'social' | 'batch' | 'active-learning' | 'settings'>('home');
  
  // Dark mode state
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const saved = localStorage.getItem('bg_theme');
    return (saved === 'light' || saved === 'dark') ? saved : 'dark';
  });

  const toggleTheme = () => setTheme(prev => prev === 'dark' ? 'light' : 'dark');

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('bg_theme', theme);
  }, [theme]);

  // Settings states
  const [apiUrl, setApiUrl] = useState(() => localStorage.getItem('bg_api_url') || 'http://localhost:8000');
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('bg_api_key') || '');
  const [apiStatus, setApiStatus] = useState<'unchecked' | 'online' | 'offline'>('unchecked');
  const [modelStatus, setModelStatus] = useState<any>(null);

  // Keep ref of status to avoid useEffect triggers on polling delay calculation
  const apiStatusRef = useRef(apiStatus);
  useEffect(() => {
    apiStatusRef.current = apiStatus;
  }, [apiStatus]);

  // Save settings when changed
  useEffect(() => {
    localStorage.setItem('bg_api_url', apiUrl);
    localStorage.setItem('bg_api_key', apiKey);
  }, [apiUrl, apiKey]);

  const checkingRef = useRef(false);

  // Test connection to backend
  const checkConnection = useCallback(async (silent = false) => {
    if (checkingRef.current) return false;
    checkingRef.current = true;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000); // 2s timeout for connection check

    try {
      if (!silent) setApiStatus('unchecked');
      const headers: Record<string, string> = {};
      if (apiKey) headers['x-api-key'] = apiKey;

      const healthRes = await fetch(`${apiUrl}/health?_t=${Date.now()}`, { 
        headers,
        signal: controller.signal,
        cache: 'no-store'
      });
      clearTimeout(timeoutId);
      
      if (!healthRes.ok) throw new Error('Health check failed');
      
      // Fetch models status if health check succeeds
      const statusController = new AbortController();
      const statusTimeoutId = setTimeout(() => statusController.abort(), 2000);
      try {
        const statusRes = await fetch(`${apiUrl}/models/status?_t=${Date.now()}`, { 
          headers,
          signal: statusController.signal,
          cache: 'no-store'
        });
        clearTimeout(statusTimeoutId);
        if (statusRes.ok) {
          const statusData = await statusRes.json();
          setModelStatus(statusData);
        }
      } catch (statusErr) {
        clearTimeout(statusTimeoutId);
        console.warn('Gagal mengambil status model:', statusErr);
      }

      setApiStatus('online');
      if (!silent) toast.success('Berhasil terhubung ke FastAPI backend!');
      checkingRef.current = false;
      return true;
    } catch (err: any) {
      clearTimeout(timeoutId);
      setApiStatus('offline');
      setModelStatus(null);
      if (!silent) toast.error('Gagal terhubung ke backend. Menjalankan simulasi sandbox offline.');
      checkingRef.current = false;
      return false;
    }
  }, [apiUrl, apiKey]);

  // Perform dynamic polling checks
  useEffect(() => {
    let timerId: any;

    const runCheck = async () => {
      await checkConnection(true);
      const delay = apiStatusRef.current === 'offline' ? 3000 : 15000;
      timerId = setTimeout(runCheck, delay);
    };

    timerId = setTimeout(runCheck, 100);

    return () => clearTimeout(timerId);
  }, [checkConnection]);

  // Export Results to CSV
  const handleExportCSV = (data: any[]) => {
    if (data.length === 0) return;
    
    let csvContent = 'Text,Is Toxic,Is Bully,Category,Reason\n';
    
    data.forEach(item => {
      const escapedText = item.text.replace(/"/g, '""').replace(/\n/g, ' ');
      const escapedReason = (item.reason || '').replace(/"/g, '""').replace(/\n/g, ' ');
      csvContent += `"${escapedText}",${item.is_toxic},${item.is_bully},"${item.category}","${escapedReason}"\n`;
    });
    
    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `bullyguard_report_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    toast.success('Laporan CSV berhasil diunduh!');
  };

  return (
    <MotionConfig reducedMotion="user">
        <LazyMotion features={domAnimation}>
          <div className="min-h-screen flex flex-col font-sans overflow-x-hidden relative selection:bg-blue-100 selection:text-blue-900">
          <Toaster position="top-right" richColors theme={theme} />
      
      {/* Background Decorative Elements */}
      <div className="fixed inset-0 z-0 pointer-events-none hero-gradient" />
      <div className={`fixed top-20 left-[-10%] w-[40%] h-[40%] rounded-full blur-3xl z-0 pointer-events-none ${theme === 'dark' ? 'bg-blue-500/5 opacity-30' : 'bg-blue-200/20 opacity-50'}`} />
      <div className={`fixed bottom-20 right-[-10%] w-[30%] h-[50%] rounded-full blur-3xl z-0 pointer-events-none ${theme === 'dark' ? 'bg-purple-500/5 opacity-30' : 'bg-purple-200/30 opacity-50'}`} />

      {/* Main Layout Container */}
      <div className={`flex flex-col md:flex-row flex-grow relative z-10 w-full ${
        activeTab !== 'home' ? 'h-screen overflow-hidden' : 'min-h-screen'
      }`}>
        {/* Render Sidebar conditionally on Dashboard pages */}
        {activeTab !== 'home' && (
          <Sidebar 
            activeTab={activeTab} 
            setActiveTab={setActiveTab} 
            apiStatus={apiStatus}
            theme={theme}
            toggleTheme={toggleTheme}
          />
        )}
        
        <div className={`flex-grow flex flex-col min-w-0 ${activeTab !== 'home' ? 'h-full overflow-hidden' : ''}`}>
          {/* Main Content Area */}
          <main 
            data-lenis-prevent
            className={`flex-grow relative w-full ${
              activeTab === 'home' 
                ? 'max-w-7xl mx-auto px-6 pb-16 pt-8' 
                : 'p-6 md:p-8 overflow-y-auto h-full'
            }`}
          >
            <AnimatePresence mode="wait">
              {activeTab === 'home' && (
                <Home 
                  key="home" 
                  setActiveTab={setActiveTab} 
                  theme={theme} 
                  toggleTheme={toggleTheme} 
                  apiStatus={apiStatus} 
                  apiUrl={apiUrl}
                  apiKey={apiKey}
                />
              )}
              {activeTab === 'detector' && (
                <Detector key="detector" apiUrl={apiUrl} apiKey={apiKey} />
              )}
              {activeTab === 'social' && (
                <SocialScraper 
                  key="social" 
                  apiUrl={apiUrl} 
                  apiKey={apiKey} 
                  handleExportCSV={handleExportCSV} 
                />
              )}
              {activeTab === 'batch' && (
                <BatchAnalysis 
                  key="batch" 
                  apiUrl={apiUrl} 
                  apiKey={apiKey} 
                  handleExportCSV={handleExportCSV} 
                />
              )}
              {activeTab === 'active-learning' && (
                <ActiveLearning 
                  key="active" 
                  apiUrl={apiUrl} 
                  apiKey={apiKey} 
                  checkConnection={checkConnection} 
                />
              )}
              {activeTab === 'settings' && (
                <Settings 
                  key="settings" 
                  apiUrl={apiUrl} 
                  setApiUrl={setApiUrl} 
                  apiKey={apiKey} 
                  setApiKey={setApiKey} 
                  checkConnection={checkConnection} 
                  modelStatus={modelStatus} 
                />
              )}
            </AnimatePresence>
          </main>

          {/* Footer - only rendered on Landing Page */}
          {activeTab === 'home' && (
            <footer className="w-full py-8 bg-gray-50/50 border-t border-gray-100 z-10 relative mt-auto">
              <div className="flex flex-col md:flex-row justify-between items-center px-6 max-w-7xl mx-auto gap-4">
                <div className="font-black text-sm" style={{ color: 'var(--text-color)' }}>
                  BullyGuard ID
                </div>
                <div className="flex flex-wrap justify-center gap-4 text-xs font-semibold" style={{ color: 'var(--text-muted)' }}>
                  <a href="#" className="hover:text-blue-600 transition-colors">Kebijakan Privasi</a>
                  <a href="#" className="hover:text-blue-600 transition-colors">Panduan AI Etis</a>
                  <a href="#" className="hover:text-blue-600 transition-colors">Dokumentasi API</a>
                  <a href="#" className="hover:text-blue-600 transition-colors">Dukungan</a>
                </div>
                <div className="text-xs text-center md:text-right" style={{ color: 'var(--text-muted)' }}>
                  © 2026 BullyGuard ID. Safeguarding digital spaces with Ethical AI.
                </div>
              </div>
            </footer>
          )}
        </div>
      </div>
        </div>
        </LazyMotion>
      </MotionConfig>
  );
}
