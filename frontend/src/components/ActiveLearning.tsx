import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence, LayoutGroup } from 'framer-motion';
import { toast } from 'sonner';
import FilterBar from './ActiveLearning/FilterBar';
import Quadrant from './ActiveLearning/Quadrant';
import type { QuadrantItem } from './ActiveLearning/Quadrant';
import RetrainTerminal from './ActiveLearning/RetrainTerminal';

interface CategorizedData {
  toxic_bully: QuadrantItem[];
  toxic_non_bully: QuadrantItem[];
  non_toxic_bully: QuadrantItem[];
  non_toxic_non_bully: QuadrantItem[];
}

interface ActiveLearningProps {
  apiUrl: string;
  apiKey: string;
  checkConnection: (silent: boolean) => Promise<boolean>;
}

export default function ActiveLearning({ apiUrl, apiKey, checkConnection }: ActiveLearningProps) {
  const [categorizedData, setCategorizedData] = useState<CategorizedData>({
    toxic_bully: [],
    toxic_non_bully: [],
    non_toxic_bully: [],
    non_toxic_non_bully: []
  });
  const [activeLearningLoading, setActiveLearningLoading] = useState(false);
  const [trainingLogs, setTrainingLogs] = useState<string[]>([]);
  const [isTraining, setIsTraining] = useState(false);

  // Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [decisionSourceFilter, setDecisionSourceFilter] = useState('');
  const [confidenceFilter, setConfidenceFilter] = useState('');

  // Selection states
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  
  const abortControllerRef = useRef<AbortController | null>(null);
  const simulationIntervalRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) abortControllerRef.current.abort();
      if (simulationIntervalRef.current) clearInterval(simulationIntervalRef.current);
    };
  }, []);

  // Fetch with query params
  const fetchActiveLearningData = async (silent = false) => {
    if (!silent) setActiveLearningLoading(true);
    const headers: Record<string, string> = {};
    if (apiKey) headers['x-api-key'] = apiKey;

    const params = new URLSearchParams();
    params.append('limit', '150');
    if (searchQuery.trim()) {
      params.append('search', searchQuery.trim());
    }
    if (decisionSourceFilter) {
      params.append('decision_source', decisionSourceFilter);
    }
    if (confidenceFilter === 'uncertain') {
      params.append('confidence_min', '0.4');
      params.append('confidence_max', '0.7');
    } else if (confidenceFilter === 'certain') {
      params.append('confidence_min', '0.8');
      params.append('confidence_max', '1.0');
    }

    try {
      const response = await fetch(`${apiUrl}/api/data/categorized?${params.toString()}`, { headers });
      if (!response.ok) throw new Error('Failed to fetch data');
      const data = await response.json();
      setCategorizedData(data);
    } catch (err: any) {
      console.error(err);
      toast.error('Gagal memuat data. Menjalankan simulasi data lokal.');
      
      // Local fallback data
      setCategorizedData({
        toxic_bully: [
          { text: 'kamu anak haram goblog bego', is_toxic: true, is_bully: true, reason: 'Mengandung makian personal.', decision_source: 'Model Core', confidence: 0.95, timestamp: '2026-06-03 14:20', is_validated: 0 },
          { text: 'mukamu jelek banget mending mati aja', is_toxic: true, is_bully: true, reason: 'Intimidasi fisik parah.', decision_source: 'Model Core', confidence: 0.91, timestamp: '2026-06-03 15:11', is_validated: 0 }
        ],
        toxic_non_bully: [
          { text: 'anjing kaget gua ada kucing lompat', is_toxic: true, is_bully: false, reason: 'Bahasa kasar non-penyerangan.', decision_source: 'Lexicon Match', confidence: 0.85, timestamp: '2026-06-03 16:05', is_validated: 0 },
          { text: 'hebat banget asu dapet nilai a!', is_toxic: true, is_bully: false, reason: 'Slang pujian bermakna kagum.', decision_source: 'Model Core', confidence: 0.72, timestamp: '2026-06-03 16:45', is_validated: 0 }
        ],
        non_toxic_bully: [
          { text: 'pinter banget kamu ya sampe ga lulus ujian', is_toxic: false, is_bully: true, reason: 'Sarkasme halus meremehkan.', decision_source: 'Transformers', confidence: 0.88, timestamp: '2026-06-03 12:10', is_validated: 0 },
          { text: 'ganteng amat bro kayak spakbor mobil', is_toxic: false, is_bully: true, reason: 'Ejekan sarkastik terselubung.', decision_source: 'Transformers', confidence: 0.81, timestamp: '2026-06-03 13:00', is_validated: 0 }
        ],
        non_toxic_non_bully: [
          { text: 'selamat ya atas peluncuran aplikasi barunya!', is_toxic: false, is_bully: false, reason: 'Komentar aman dan apresiatif.', decision_source: 'Lexicon Match', confidence: 0.99, timestamp: '2026-06-03 10:15', is_validated: 1 },
          { text: 'apakah besok kita ada tugas kuliah kelompok?', is_toxic: false, is_bully: false, reason: 'Pertanyaan netral.', decision_source: 'Lexicon Match', confidence: 0.98, timestamp: '2026-06-03 11:30', is_validated: 0 }
        ]
      });
    } finally {
      setActiveLearningLoading(false);
    }
  };

  // Debounced filter application
  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      fetchActiveLearningData();
    }, 350);
    return () => clearTimeout(delayDebounce);
  }, [searchQuery, decisionSourceFilter, confidenceFilter]);

  // Selection handlers
  const handleSelectItem = (text: string, checked: boolean) => {
    if (checked) {
      setSelectedItems(prev => [...prev, text]);
    } else {
      setSelectedItems(prev => prev.filter(t => t !== text));
    }
  };

  const handleSelectAll = (quadrant: keyof CategorizedData, checked: boolean) => {
    const items = categorizedData[quadrant].map(i => i.text);
    if (checked) {
      setSelectedItems(prev => {
        const next = [...prev];
        items.forEach(text => {
          if (!next.includes(text)) next.push(text);
        });
        return next;
      });
    } else {
      setSelectedItems(prev => prev.filter(text => !items.includes(text)));
    }
  };

  // Single Reallocate
  const handleReallocate = async (text: string, newIsToxic: boolean, newIsBully: boolean) => {
    // 1. Optimistic Update (instantly move the card on the frontend)
    setCategorizedData(prev => {
      let foundItem: QuadrantItem | null = null;
      const keys: (keyof CategorizedData)[] = ['toxic_bully', 'toxic_non_bully', 'non_toxic_bully', 'non_toxic_non_bully'];
      
      const updated: CategorizedData = {
        toxic_bully: [...prev.toxic_bully],
        toxic_non_bully: [...prev.toxic_non_bully],
        non_toxic_bully: [...prev.non_toxic_bully],
        non_toxic_non_bully: [...prev.non_toxic_non_bully]
      };

      for (const k of keys) {
        const index = updated[k].findIndex(item => item.text === text);
        if (index !== -1) {
          foundItem = updated[k].splice(index, 1)[0];
          break;
        }
      }

      if (foundItem) {
        const updatedItem = {
          ...foundItem,
          is_toxic: newIsToxic,
          is_bully: newIsBully,
          is_validated: 1
        };
        
        let destKey: keyof CategorizedData = 'non_toxic_non_bully';
        if (newIsToxic && newIsBully) destKey = 'toxic_bully';
        else if (newIsToxic && !newIsBully) destKey = 'toxic_non_bully';
        else if (!newIsToxic && newIsBully) destKey = 'non_toxic_bully';

        if (!updated[destKey].some(i => i.text === text)) {
          updated[destKey] = [updatedItem, ...updated[destKey]];
        }
      }
      return updated;
    });

    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (apiKey) headers['x-api-key'] = apiKey;

    try {
      const response = await fetch(`${apiUrl}/api/data/reallocate`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          text,
          new_is_toxic: newIsToxic,
          new_is_bully: newIsBully
        })
      });

      if (!response.ok) throw new Error('Reallocate failed');
      const data = await response.json();
      if (data.success) {
        toast.success('Kategori data berhasil diubah & divalidasi!');
        // 2. Silent background refresh to sync DB state without flashing "Memuat data..."
        fetchActiveLearningData(true);
      } else {
        toast.error(data.message || 'Gagal mengubah kategori.');
        // Revert on error by doing a full reload
        fetchActiveLearningData(false);
      }
    } catch (err: any) {
      console.error(err);
      toast.success('Simulasi: Sukses mengubah label data di sandbox lokal.');
    }
  };

  // Bulk Reallocate & Validate Action
  const handleBulkReallocate = async (newIsToxic: boolean | null, newIsBully: boolean | null) => {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (apiKey) headers['x-api-key'] = apiKey;

    const itemsToUpdate = selectedItems.map(text => {
      let isToxic = newIsToxic;
      let isBully = newIsBully;

      if (newIsToxic === null && newIsBully === null) {
        const found = 
          categorizedData.toxic_bully.find(i => i.text === text) ||
          categorizedData.toxic_non_bully.find(i => i.text === text) ||
          categorizedData.non_toxic_bully.find(i => i.text === text) ||
          categorizedData.non_toxic_non_bully.find(i => i.text === text);

        isToxic = found ? found.is_toxic : false;
        isBully = found ? found.is_bully : false;
      }

      return {
        text,
        new_is_toxic: !!isToxic,
        new_is_bully: !!isBully
      };
    });

    try {
      const response = await fetch(`${apiUrl}/api/data/reallocate/bulk`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ items: itemsToUpdate })
      });

      if (!response.ok) throw new Error('Bulk action failed');
      const data = await response.json();
      if (data.success) {
        toast.success(data.message || 'Tindakan massal berhasil diterapkan!');
        setSelectedItems([]);
        fetchActiveLearningData();
      } else {
        toast.error(data.message || 'Gagal menerapkan tindakan massal.');
      }
    } catch (err: any) {
      console.error(err);
      toast.success('Simulasi: Sukses melakukan relokasi massal di sandbox lokal.');
      
      setCategorizedData(prev => {
        const updated: CategorizedData = {
          toxic_bully: [...prev.toxic_bully],
          toxic_non_bully: [...prev.toxic_non_bully],
          non_toxic_bully: [...prev.non_toxic_bully],
          non_toxic_non_bully: [...prev.non_toxic_non_bully]
        };

        itemsToUpdate.forEach(item => {
          let foundItem: QuadrantItem | null = null;
          const keys: (keyof CategorizedData)[] = ['toxic_bully', 'toxic_non_bully', 'non_toxic_bully', 'non_toxic_non_bully'];

          for (const k of keys) {
            const idx = updated[k].findIndex(i => i.text === item.text);
            if (idx !== -1) {
              foundItem = updated[k].splice(idx, 1)[0];
              break;
            }
          }

          if (foundItem) {
            const updatedItem = {
              ...foundItem,
              is_toxic: item.new_is_toxic,
              is_bully: item.new_is_bully,
              is_validated: 1
            };

            let destKey: keyof CategorizedData = 'non_toxic_non_bully';
            if (item.new_is_toxic && item.new_is_bully) destKey = 'toxic_bully';
            else if (item.new_is_toxic && !item.new_is_bully) destKey = 'toxic_non_bully';
            else if (!item.new_is_toxic && item.new_is_bully) destKey = 'non_toxic_bully';

            updated[destKey] = [updatedItem, ...updated[destKey]];
          }
        });

        return updated;
      });
      setSelectedItems([]);
    }
  };

  const handleStartTraining = async () => {
    if (isTraining) return;
    setIsTraining(true);
    setTrainingLogs([]);
    
    const headers: Record<string, string> = {};
    if (apiKey) headers['x-api-key'] = apiKey;

    try {
      const response = await fetch(`${apiUrl}/api/train/start`, {
        method: 'POST',
        headers
      });

      if (!response.ok) throw new Error('Failed to start training');
      const data = await response.json();
      
      if (data.success) {
        toast.success('Proses pelatihan ulang berhasil dipicu di backend!');
        startReadingLogs();
      } else {
        toast.error(data.message || 'Pelatihan sudah berjalan.');
        setIsTraining(false);
      }
    } catch (err: any) {
      console.error(err);
      toast.info('Gagal memicu pelatihan di server. Menjalankan simulasi training log.');
      simulateTrainingLogs();
    }
  };

  const startReadingLogs = async () => {
    const headers: Record<string, string> = { 'Accept': 'text/event-stream' };
    if (apiKey) headers['x-api-key'] = apiKey;

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      const response = await fetch(`${apiUrl}/api/train/logs`, { 
        headers,
        signal: abortController.signal
      });
      if (!response.ok) throw new Error('Log stream failed');

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) return;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const content = line.substring(6).trim();
            if (content) {
              setTrainingLogs(prev => [...prev, content]);
              
              if (content.includes('[SELESAI]') || content.includes('sukses!')) {
                setIsTraining(false);
                toast.success('Pelatihan ulang model selesai!');
                checkConnection(true);
              }
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        console.log('Pembacaan log stream dibatalkan.');
        return;
      }
      console.error(err);
      toast.error('Koneksi log stream terputus.');
      setIsTraining(false);
    }
  };

  const simulateTrainingLogs = () => {
    const logs = [
      '=== Memulai Pelatihan Ulang (Background Process) ===',
      'Memuat leksikon dan kamus slang...',
      'Ditemukan 5 file scraper baru untuk diintegrasikan.',
      'Mengimpor 174 baris data dari classification_memory (validated).',
      'Melakukan oversampling x5 untuk sampel validasi active learning...',
      'Menggabungkan dataset kombinasi: Total 11.450 baris data.',
      'Melakukan stratifikasi data latih dan uji (split 85/15)...',
      'Melakukan augmentasi teks sarkasme & slang pujian...',
      'Melatih model Klasifikasi Multi-Label (Logistic Regression C=1.5)...',
      'Iterasi 100/1500 - Loss: 0.456',
      'Iterasi 300/1500 - Loss: 0.231',
      'Iterasi 600/1500 - Loss: 0.108',
      'Melakukan evaluasi threshold terkalibrasi...',
      'Threshold Optimal -> Toxic: 0.45 | Bully: 0.55',
      'F1-Score Model Baru -> Toxic: 0.8920 | Bully: 0.8654',
      'F1-Score Model Lama -> Toxic: 0.8710 | Bully: 0.8410',
      'Peningkatan performa terdeteksi. Menyimpan model versi terbaru...',
      'Menyimpan file model_lr.joblib dan thresholds.json.',
      'Metadata disimpan ke current_model_version.json.',
      '[SELESAI] Proses pelatihan telah selesai. Model aktif telah diperbarui!'
    ];

    let i = 0;
    if (simulationIntervalRef.current) {
      clearInterval(simulationIntervalRef.current);
    }
    simulationIntervalRef.current = window.setInterval(() => {
      if (i < logs.length) {
        setTrainingLogs(prev => [...prev, logs[i]]);
        i++;
      } else {
        if (simulationIntervalRef.current) {
          clearInterval(simulationIntervalRef.current);
          simulationIntervalRef.current = null;
        }
        setIsTraining(false);
        toast.success('Model berhasil diperbarui (simulasi)!');
      }
    }, 400);
  };

  const handleExport = (format: 'csv' | 'json') => {
    const allItems = [
      ...categorizedData.toxic_bully,
      ...categorizedData.toxic_non_bully,
      ...categorizedData.non_toxic_bully,
      ...categorizedData.non_toxic_non_bully
    ];

    if (allItems.length === 0) {
      toast.warning('Tidak ada data active learning untuk diekspor!');
      return;
    }

    if (format === 'json') {
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(allItems, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `bullyguard_dataset_${new Date().toISOString().split('T')[0]}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      toast.success('Dataset format JSON berhasil diunduh!');
    } else {
      // Export as CSV
      const headers = ['Text', 'Is_Toxic', 'Is_Bully', 'Reason', 'Decision_Source', 'Confidence', 'Timestamp', 'Is_Validated'];
      const rows = allItems.map(item => [
        `"${item.text.replace(/"/g, '""')}"`,
        item.is_toxic ? 1 : 0,
        item.is_bully ? 1 : 0,
        `"${item.reason.replace(/"/g, '""')}"`,
        `"${item.decision_source.replace(/"/g, '""')}"`,
        item.confidence.toFixed(4),
        `"${item.timestamp}"`,
        item.is_validated
      ]);

      const csvContent = "data:text/csv;charset=utf-8," 
        + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
      
      const encodedUri = encodeURI(csvContent);
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", encodedUri);
      downloadAnchor.setAttribute("download", `bullyguard_dataset_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      toast.success('Dataset format CSV berhasil diunduh!');
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -15 }}
      transition={{ duration: 0.3 }}
      className="py-6 flex flex-col gap-6"
    >
      <header className="mb-2">
        <h1 className="text-3xl font-black text-gray-900 mb-1">Human-in-the-Loop Active Learning</h1>
        <p className="text-gray-500 text-sm">Jika ada kesalahan klasifikasi slang lokal oleh AI, koreksi secara manual di sini untuk melatih ulang model.</p>
      </header>

      {/* Filter Bar */}
      <FilterBar
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        decisionSourceFilter={decisionSourceFilter}
        setDecisionSourceFilter={setDecisionSourceFilter}
        confidenceFilter={confidenceFilter}
        setConfidenceFilter={setConfidenceFilter}
        onRefresh={fetchActiveLearningData}
        onExport={handleExport}
        isLoading={activeLearningLoading}
      />

      {/* Quadrant display */}
      <LayoutGroup id="active-learning-quadrants">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Quadrant
          title="Bully-toxic(bully)"
          items={categorizedData.toxic_bully}
          theme="rose"
          selectedItems={selectedItems}
          onDrop={(text) => handleReallocate(text, true, true)}
          onSelectItem={handleSelectItem}
          onSelectAll={(checked) => handleSelectAll('toxic_bully', checked)}
          onReallocate={handleReallocate}
          isLoading={activeLearningLoading}
        />

        <Quadrant
          title="Toxic non-bully(slang)"
          items={categorizedData.toxic_non_bully}
          theme="amber"
          selectedItems={selectedItems}
          onDrop={(text) => handleReallocate(text, true, false)}
          onSelectItem={handleSelectItem}
          onSelectAll={(checked) => handleSelectAll('toxic_non_bully', checked)}
          onReallocate={handleReallocate}
          isLoading={activeLearningLoading}
        />

        <Quadrant
          title="non-Toxic Bully(Sarkasme)"
          items={categorizedData.non_toxic_bully}
          theme="purple"
          selectedItems={selectedItems}
          onDrop={(text) => handleReallocate(text, false, true)}
          onSelectItem={handleSelectItem}
          onSelectAll={(checked) => handleSelectAll('non_toxic_bully', checked)}
          onReallocate={handleReallocate}
          isLoading={activeLearningLoading}
        />

        <Quadrant
          title="non-toxic non-bully(Normal)"
          items={categorizedData.non_toxic_non_bully}
          theme="emerald"
          selectedItems={selectedItems}
          onDrop={(text) => handleReallocate(text, false, false)}
          onSelectItem={handleSelectItem}
          onSelectAll={(checked) => handleSelectAll('non_toxic_non_bully', checked)}
          onReallocate={handleReallocate}
          isLoading={activeLearningLoading}
        />
      </div>
    </LayoutGroup>

      {/* Floating Action Bar */}
      <AnimatePresence>
        {selectedItems.length > 0 && (
          <motion.div 
            initial={{ opacity: 0, y: 50, x: "-50%" }}
            animate={{ opacity: 1, y: 0, x: "-50%" }}
            exit={{ opacity: 0, y: 50, x: "-50%" }}
            className="fixed bottom-6 left-1/2 z-50 bg-white/90 backdrop-blur-md border border-gray-200 px-6 py-4 rounded-2xl shadow-2xl flex items-center gap-4 flex-wrap max-w-full"
          >
            <div className="flex flex-col gap-0.5">
              <span className="text-xs font-black text-gray-900">
                {selectedItems.length} teks terpilih
              </span>
              <span className="text-[10px] font-bold text-gray-400 uppercase">Tindakan Massal</span>
            </div>
            
            <div className="h-6 w-px bg-gray-200" />
            
            <div className="flex gap-2 flex-wrap">
              <button
                onClick={() => handleBulkReallocate(true, true)}
                className="bg-rose-600 text-white text-[10px] font-bold px-3 py-2 rounded-lg hover:bg-rose-700 transition cursor-pointer border-none"
              >
                Bully-toxic(bully)
              </button>
              <button
                onClick={() => handleBulkReallocate(true, false)}
                className="bg-amber-500 text-white text-[10px] font-bold px-3 py-2 rounded-lg hover:bg-amber-600 transition cursor-pointer border-none"
              >
                Toxic non-bully(slang)
              </button>
              <button
                onClick={() => handleBulkReallocate(false, true)}
                className="bg-purple-600 text-white text-[10px] font-bold px-3 py-2 rounded-lg hover:bg-purple-700 transition cursor-pointer border-none"
              >
                non-Toxic Bully(Sarkasme)
              </button>
              <button
                onClick={() => handleBulkReallocate(false, false)}
                className="bg-emerald-600 text-white text-[10px] font-bold px-3 py-2 rounded-lg hover:bg-emerald-700 transition cursor-pointer border-none"
              >
                non-toxic non-bully(Normal)
              </button>
              <button
                onClick={() => handleBulkReallocate(null, null)}
                className="bg-blue-600 text-white text-[10px] font-bold px-3 py-2 rounded-lg hover:bg-blue-700 transition cursor-pointer border-none"
              >
                Validasi Saja
              </button>
            </div>
            
            <div className="h-6 w-px bg-gray-200" />
            
            <button
              onClick={() => setSelectedItems([])}
              className="text-gray-500 hover:text-gray-700 text-xs font-bold cursor-pointer bg-transparent border-none"
            >
              Batal
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Retrain Controls & Console Log */}
      <RetrainTerminal
        onStartTraining={handleStartTraining}
        isTraining={isTraining}
        trainingLogs={trainingLogs}
        onClearLogs={() => setTrainingLogs([])}
      />
    </motion.div>
  );
}
