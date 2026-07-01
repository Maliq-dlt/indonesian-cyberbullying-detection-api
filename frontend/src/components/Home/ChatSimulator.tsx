import React, { useState, useEffect } from 'react';
import { m, AnimatePresence } from 'framer-motion';
import { Shield, Activity } from 'lucide-react';

export const simulatedComments = [
  {
    author: "user_anon88",
    avatar: "A",
    text: "Terima kasih atas bantuannya hari ini, sangat terbantu sekali! Sukses selalu.",
    verdict: "Aman / Bersih",
    confidence: 0.99,
    details: "Teks dianalisis aman dari indikasi cyberbullying, ujaran kebencian, atau pelecehan.",
    type: "aman",
    segments: [
      { text: "Terima kasih atas bantuannya hari ini, sangat terbantu sekali! Sukses selalu." }
    ]
  },
  {
    author: "hater_detect32",
    avatar: "H",
    text: "eh lu bego banget sih kerja ginian aja ga becus wkwk mental lemah",
    verdict: "Toxic & Bullying",
    confidence: 0.95,
    details: "Mengandung makian personal kasar dan ejekan merendahkan kapasitas mental seseorang.",
    type: "toxic-bully",
    segments: [
      { text: "eh lu " },
      { text: "bego", type: "toxic", weight: 0.85 },
      { text: " banget sih kerja ginian aja " },
      { text: "ga becus", type: "toxic", weight: 0.75 },
      { text: " wkwk " },
      { text: "mental lemah", type: "bully", weight: 0.90 }
    ]
  },
  {
    author: "gamer_id90",
    avatar: "G",
    text: "anjing kaget gua kirain musuhnya udah mati ternyata masih hidup kampret",
    verdict: "Toxic but Non-Bully",
    confidence: 0.88,
    details: "Mengandung kata kasar/umpatan mengekspresikan emosi kekagetan, bukan serangan personal.",
    type: "toxic-nonbully",
    segments: [
      { text: "anjing", type: "toxic", weight: 0.88 },
      { text: " kaget gua kirain musuhnya udah mati ternyata masih hidup " },
      { text: "kampret", type: "toxic", weight: 0.70 }
    ]
  },
  {
    author: "sarcasm_king",
    avatar: "S",
    text: "pinter banget sih kamu ya, sampe-sampe nilai ujiannya dapet nol terus",
    verdict: "Non-Toxic but Bully",
    confidence: 0.84,
    details: "Sarkasme halus meremehkan inteligensi orang lain secara pasif-agresif.",
    type: "nontoxic-bully",
    segments: [
      { text: "pinter banget sih", type: "bully", weight: 0.65 },
      { text: " kamu ya, sampe-sampe " },
      { text: "nilai ujiannya dapet nol terus", type: "bully", weight: 0.82 }
    ]
  }
];

export default function ChatSimulator() {
  const [index, setIndex] = useState(0);
  const [textToShow, setTextToShow] = useState('');
  const [stage, setStage] = useState<'typing' | 'scanning' | 'revealing' | 'idle'>('typing');
  const [typedLength, setTypedLength] = useState(0);
  
  const currentComment = simulatedComments[index];
  const fullText = currentComment.text;

  useEffect(() => {
    if (stage !== 'typing') return;
    if (typedLength < fullText.length) {
      const timer = setTimeout(() => {
        setTypedLength(prev => prev + 1);
        setTextToShow(fullText.slice(0, typedLength + 1));
      }, 35 + Math.random() * 25);
      return () => clearTimeout(timer);
    } else {
      const timer = setTimeout(() => { setStage('scanning'); }, 800);
      return () => clearTimeout(timer);
    }
  }, [stage, typedLength, fullText]);

  useEffect(() => {
    if (stage !== 'scanning') return;
    const timer = setTimeout(() => { setStage('revealing'); }, 1800);
    return () => clearTimeout(timer);
  }, [stage]);

  useEffect(() => {
    if (stage !== 'revealing') return;
    const timer = setTimeout(() => { setStage('idle'); }, 1000);
    return () => clearTimeout(timer);
  }, [stage]);

  useEffect(() => {
    if (stage !== 'idle') return;
    const timer = setTimeout(() => {
      setStage('typing');
      setTypedLength(0);
      setTextToShow('');
      setIndex(prev => (prev + 1) % simulatedComments.length);
    }, 4000);
    return () => clearTimeout(timer);
  }, [stage]);

  const config = {
    aman: { badgeClass: "bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-100 dark:border-emerald-500/20", progressClass: "bg-emerald-500", textClass: "text-emerald-800 dark:text-emerald-400" },
    'toxic-bully': { badgeClass: "bg-rose-50 dark:bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-105 dark:border-rose-500/20", progressClass: "bg-rose-600", textClass: "text-rose-800 dark:text-rose-400" },
    'toxic-nonbully': { badgeClass: "bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-100 dark:border-amber-500/20", progressClass: "bg-amber-500", textClass: "text-amber-800 dark:text-amber-400" },
    'nontoxic-bully': { badgeClass: "bg-purple-50 dark:bg-purple-500/10 text-purple-700 dark:text-purple-400 border-purple-100 dark:border-purple-500/20", progressClass: "bg-purple-600", textClass: "text-purple-800 dark:text-purple-400" }
  }[currentComment.type as 'aman' | 'toxic-bully' | 'toxic-nonbully' | 'nontoxic-bully'] || { badgeClass: "bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-100 dark:border-emerald-500/20", progressClass: "bg-emerald-500", textClass: "text-emerald-800 dark:text-emerald-400" };

  return (
    <div className="relative glass-card rounded-2xl p-6 border border-white/60 dark:border-white/10 shadow-xl overflow-hidden min-h-[300px] flex flex-col justify-between">
      {stage === 'scanning' && (
        <m.div initial={{ top: '0%' }} animate={{ top: '100%' }} transition={{ repeat: Infinity, repeatType: "reverse", duration: 0.9, ease: "linear" }} className="absolute left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-blue-500/80 to-transparent pointer-events-none shadow-[0_0_10px_rgba(59,130,246,0.8)] z-20" />
      )}

      <div className="flex justify-between items-center mb-4 border-b border-gray-150 dark:border-gray-800/60 pb-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-blue-50 dark:bg-blue-500/10 flex items-center justify-center text-blue-600 dark:text-blue-400 shrink-0">
            <Shield className="w-4.5 h-4.5" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-gray-900 dark:text-[#faf8ff] leading-none">Analisis Real-Time</h3>
            <span className="text-[9px] text-gray-400 font-bold uppercase tracking-wider mt-0.5 block leading-none">AI Hybrid Scanner</span>
          </div>
        </div>
        <span className="bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 px-2 py-0.5 rounded text-[10px] font-bold flex items-center gap-1 border border-emerald-100 dark:border-emerald-500/20 leading-none">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" /> Active
        </span>
      </div>

      <div className="bg-gray-50/50 dark:bg-black/10 rounded-xl p-4 border border-gray-150 dark:border-gray-800/60 mb-4 flex-grow flex flex-col justify-center min-h-[90px] relative">
        {stage === 'scanning' && (<div className="absolute inset-0 bg-blue-500/3 dark:bg-blue-500/5 animate-pulse pointer-events-none" />)}
        <div className="flex gap-2.5 mb-2.5 items-center">
          <div className="w-6.5 h-6.5 rounded-full bg-indigo-50 dark:bg-indigo-500/10 border border-indigo-100 dark:border-indigo-500/20 flex items-center justify-center text-indigo-600 dark:text-indigo-400 font-bold text-xs shrink-0 select-none">
            {currentComment.avatar}
          </div>
          <div className="flex flex-col">
            <span className="text-xs font-bold text-gray-850 dark:text-gray-200 leading-none">{currentComment.author}</span>
            <span className="text-[9px] text-gray-400 font-semibold leading-none mt-1">Baru saja</span>
          </div>
        </div>
        <p className="text-xs text-gray-700 dark:text-gray-300 italic font-medium leading-relaxed">
          "{stage === 'typing' || stage === 'scanning' ? textToShow : currentComment.segments.map((seg, idx) => {
            if (seg.type === 'toxic') return <span key={idx} className="bg-rose-500/15 text-rose-700 dark:bg-rose-500/25 dark:text-rose-300 font-bold px-1.5 py-0.5 rounded border-b-2 border-rose-400/60 transition-colors">{seg.text}</span>;
            else if (seg.type === 'bully') return <span key={idx} className="bg-purple-500/15 text-purple-700 dark:bg-purple-500/25 dark:text-purple-300 font-bold px-1.5 py-0.5 rounded border-b-2 border-purple-400/60 transition-colors">{seg.text}</span>;
            else return <span key={idx}>{seg.text}</span>;
          })}"
        </p>
      </div>

      <div className="min-h-[72px] flex items-center justify-center">
        <AnimatePresence mode="wait">
          {(stage === 'revealing' || stage === 'idle') ? (
            <m.div key={index} initial={{ opacity: 0, y: 15, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: -10, scale: 0.98 }} transition={{ type: "spring", stiffness: 350, damping: 25 }} className={`w-full border rounded-xl p-3.5 flex items-start gap-3 shadow-xxs ${config.badgeClass}`}>
              <div className="flex-grow">
                <div className="flex items-center justify-between mb-1">
                  <h4 className={`text-xs font-black leading-none ${config.textClass}`}>{currentComment.verdict}</h4>
                  <span className="text-[9px] font-black bg-white/90 dark:bg-black/20 border border-current px-1.5 py-0.5 rounded leading-none shrink-0">{Math.round(currentComment.confidence * 100)}% Confidence</span>
                </div>
                <p className="text-[10px] text-gray-500 dark:text-gray-400 font-medium leading-normal">{currentComment.details}</p>
                <div className="mt-2.5 w-full bg-white/60 dark:bg-black/20 h-1 rounded-full overflow-hidden border border-black/5">
                  <m.div initial={{ width: 0 }} animate={{ width: `${currentComment.confidence * 100}%` }} transition={{ duration: 0.8, ease: "easeOut" }} className={`h-full rounded-full ${config.progressClass}`} />
                </div>
              </div>
            </m.div>
          ) : stage === 'scanning' ? (
            <m.div key="scanning-state" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="text-center py-3 flex flex-col items-center gap-1.5">
              <Activity className="w-5 h-5 text-blue-500 animate-pulse" />
              <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest animate-pulse">Memindai Konten Teks...</span>
            </m.div>
          ) : (
            <m.div key="idle-state" initial={{ opacity: 0 }} animate={{ opacity: 0.4 }} exit={{ opacity: 0 }} className="text-center py-4 text-[10px] font-bold text-gray-400 uppercase tracking-wider">Menunggu input komentar...</m.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
