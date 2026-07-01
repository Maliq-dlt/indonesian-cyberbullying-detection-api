/**
 * BullyGuard ID — Zustand Global Store
 *
 * Menggantikan prop drilling dari App.tsx ke seluruh komponen anak.
 * State yang dishare: tab navigasi, tema, konfigurasi API, koneksi status, model status.
 */

import { create } from 'zustand';
import { toast } from 'sonner';

export type TabId = 'home' | 'detector' | 'social' | 'batch' | 'active-learning' | 'settings';
export type ThemeMode = 'light' | 'dark';
export type ApiStatus = 'unchecked' | 'online' | 'offline';

interface AppState {
  // ── Navigation ────────────────────────────────────────────────────────────────
  activeTab: TabId;
  setActiveTab: (tab: TabId) => void;

  // ── Theme ─────────────────────────────────────────────────────────────────────
  theme: ThemeMode;
  toggleTheme: () => void;

  // ── API Configuration ─────────────────────────────────────────────────────────
  apiUrl: string;
  setApiUrl: (url: string) => void;
  apiKey: string;
  setApiKey: (key: string) => void;

  // ── Connection Status ─────────────────────────────────────────────────────────
  apiStatus: ApiStatus;
  setApiStatus: (status: ApiStatus) => void;
  modelStatus: any;
  setModelStatus: (status: any) => void;

  // ── Actions ───────────────────────────────────────────────────────────────────
  checkConnection: (silent?: boolean) => Promise<boolean>;
  handleExportCSV: (data: any[]) => void;
}

// Helper: simpan ke localStorage
const persist = (key: string, value: string) => {
  try { localStorage.setItem(key, value); } catch { /* quota exceeded */ }
};

let checkingRef = false;

export const useAppStore = create<AppState>((set, get) => ({
  // ── Navigation ────────────────────────────────────────────────────────────────
  activeTab: 'home',
  setActiveTab: (tab) => set({ activeTab: tab }),

  // ── Theme ─────────────────────────────────────────────────────────────────────
  theme: (() => {
    const saved = localStorage.getItem('bg_theme');
    return (saved === 'light' || saved === 'dark') ? saved : 'dark';
  })(),
  toggleTheme: () => {
    set((state) => {
      const next = state.theme === 'dark' ? 'light' : 'dark';
      persist('bg_theme', next);
      return { theme: next };
    });
  },

  // ── API Configuration ─────────────────────────────────────────────────────────
  apiUrl: localStorage.getItem('bg_api_url') || 'http://localhost:8000',
  setApiUrl: (url) => {
    persist('bg_api_url', url);
    set({ apiUrl: url });
  },
  apiKey: localStorage.getItem('bg_api_key') || '',
  setApiKey: (key) => {
    persist('bg_api_key', key);
    set({ apiKey: key });
  },

  // ── Connection Status ─────────────────────────────────────────────────────────
  apiStatus: 'unchecked',
  setApiStatus: (status) => set({ apiStatus: status }),
  modelStatus: null,
  setModelStatus: (status) => set({ modelStatus: status }),

  // ── Actions ───────────────────────────────────────────────────────────────────
  checkConnection: async (silent = false) => {
    if (checkingRef) return false;
    checkingRef = true;

    const { apiUrl, apiKey } = get();
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    try {
      if (!silent) set({ apiStatus: 'unchecked' });

      const headers: Record<string, string> = {};
      if (apiKey) headers['x-api-key'] = apiKey;

      const healthRes = await fetch(`${apiUrl}/health?_t=${Date.now()}`, {
        headers,
        signal: controller.signal,
        cache: 'no-store',
      });
      clearTimeout(timeoutId);

      if (!healthRes.ok) throw new Error('Health check failed');

      // Fetch model status
      const statusController = new AbortController();
      const statusTimeoutId = setTimeout(() => statusController.abort(), 2000);
      try {
        const statusRes = await fetch(`${apiUrl}/models/status?_t=${Date.now()}`, {
          headers,
          signal: statusController.signal,
          cache: 'no-store',
        });
        clearTimeout(statusTimeoutId);
        if (statusRes.ok) {
          const statusData = await statusRes.json();
          set({ modelStatus: statusData });
        }
      } catch {
        clearTimeout(statusTimeoutId);
      }

      set({ apiStatus: 'online' });
      if (!silent) toast.success('Berhasil terhubung ke FastAPI backend!');
      checkingRef = false;
      return true;
    } catch {
      clearTimeout(timeoutId);
      set({ apiStatus: 'offline', modelStatus: null });
      if (!silent) toast.error('Gagal terhubung ke backend. Menjalankan simulasi sandbox offline.');
      checkingRef = false;
      return false;
    }
  },

  handleExportCSV: (data) => {
    if (data.length === 0) return;

    let csvContent = 'Text,Is Toxic,Is Bully,Category,Reason\n';
    data.forEach((item) => {
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
  },
}));
