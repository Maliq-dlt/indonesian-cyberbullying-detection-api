import React from 'react';
import { motion } from 'framer-motion';
import { XAIHighlightText } from '../XAIHighlightText';
import type { WordImportance } from '../XAIHighlightText';

export interface QuadrantItem {
  text: string;
  is_toxic: boolean;
  is_bully: boolean;
  reason: string;
  decision_source: string;
  confidence: number;
  timestamp: string;
  is_validated: number;
  word_importances?: WordImportance[];
}

interface QuadrantProps {
  title: string;
  items: QuadrantItem[];
  theme: 'rose' | 'amber' | 'purple' | 'emerald';
  selectedItems: string[];
  onDrop: (text: string) => void;
  onSelectItem: (text: string, checked: boolean) => void;
  onSelectAll: (checked: boolean) => void;
  onReallocate: (text: string, isToxic: boolean, isBully: boolean) => void;
  isLoading: boolean;
}

interface QuadrantCardProps {
  item: QuadrantItem;
  theme: 'rose' | 'amber' | 'purple' | 'emerald';
  selectedItems: string[];
  config: any;
  onSelectItem: (text: string, checked: boolean) => void;
  onReallocate: (text: string, isToxic: boolean, isBully: boolean) => void;
}

function QuadrantCard({
  item,
  theme,
  selectedItems,
  config,
  onSelectItem,
  onReallocate
}: QuadrantCardProps) {
  const [isThisDragging, setIsThisDragging] = React.useState(false);

  return (
    <motion.div 
      layout 
      layoutId={item.text} 
      key={item.text}
      draggable
      onDragStart={(e: any) => {
        e.dataTransfer.setData('text/plain', item.text);
        e.dataTransfer.effectAllowed = 'move';
        // Delay the opacity class slightly so the drag image is fully opaque
        setTimeout(() => setIsThisDragging(true), 0);
      }}
      onDragEnd={() => {
        setIsThisDragging(false);
      }}
      className={`bg-white p-2.5 rounded-lg border shadow-xxs text-[11px] flex flex-col gap-1.5 cursor-grab active:cursor-grabbing hover:shadow-xs hover:border-blue-200 select-none transition-colors duration-200 ${
        selectedItems.includes(item.text) ? config.itemBorder : 'border-gray-150'
      } ${isThisDragging ? 'opacity-45 border-dashed border-blue-300 bg-gray-50/50' : ''}`}
    >
      <div className="flex items-start gap-2">
        <input
          type="checkbox"
          checked={selectedItems.includes(item.text)}
          onChange={(e) => onSelectItem(item.text, e.target.checked)}
          onClick={(e) => e.stopPropagation()}
          className={`w-3.5 h-3.5 mt-0.5 rounded border-gray-300 cursor-pointer ${config.checkboxColor}`}
        />
        <span className="font-semibold text-gray-800 flex-1 leading-relaxed">
          "<XAIHighlightText text={item.text} wordImportances={item.word_importances} />"
        </span>
      </div>
      
      <div className="flex flex-wrap items-center gap-1.5 text-[9px] mt-0.5">
        <span className="bg-gray-100 text-gray-650 px-1 py-0.5 rounded font-medium">{item.decision_source}</span>
        <span className="bg-blue-50 text-blue-700 px-1 py-0.5 rounded font-bold">Conf: {Math.round(item.confidence * 100)}%</span>
      </div>

      <div className="flex justify-between items-center mt-1 border-t border-gray-50 pt-1.5">
        <span className="text-[9px] text-gray-400 font-medium">Koreksi:</span>
        <div className="flex gap-1">
          {config.actions.map((act: any) => (
            <button 
              key={act.label}
              onClick={() => onReallocate(item.text, act.isToxic, act.isBully)} 
              className="text-[9px] bg-gray-50 text-gray-500 px-1 py-0.5 rounded border border-gray-200 hover:bg-blue-50 hover:text-blue-600 hover:border-blue-200 cursor-pointer font-bold font-sans"
            >
              {act.label}
            </button>
          ))}
        </div>
      </div>
    </motion.div>
  );
}

export default function Quadrant({
  title,
  items,
  theme,
  selectedItems,
  onDrop,
  onSelectItem,
  onSelectAll,
  onReallocate,
  isLoading
}: QuadrantProps) {
  const [isOver, setIsOver] = React.useState(false);
  
  // Config parameters based on theme
  const config = {
    rose: {
      bullet: 'bg-rose-600',
      headerBg: 'bg-rose-100/50 border-rose-200',
      textHeader: 'text-rose-800',
      textCount: 'text-rose-700 border-rose-200',
      checkboxColor: 'text-rose-600 focus:ring-rose-200',
      dragBg: 'bg-rose-50 border-rose-300 ring-4 ring-rose-100',
      itemBorder: 'border-rose-300 bg-rose-50/20',
      actions: [
        { label: 'T-NB', isToxic: true, isBully: false },
        { label: 'NT-B', isToxic: false, isBully: true },
        { label: 'Aman', isToxic: false, isBully: false }
      ]
    },
    amber: {
      bullet: 'bg-amber-500',
      headerBg: 'bg-amber-100/50 border-amber-200',
      textHeader: 'text-amber-800',
      textCount: 'text-amber-700 border-amber-200',
      checkboxColor: 'text-amber-600 focus:ring-amber-200',
      dragBg: 'bg-amber-50 border-amber-300 ring-4 ring-amber-100',
      itemBorder: 'border-amber-350 bg-amber-50/20',
      actions: [
        { label: 'T-B', isToxic: true, isBully: true },
        { label: 'NT-B', isToxic: false, isBully: true },
        { label: 'Aman', isToxic: false, isBully: false }
      ]
    },
    purple: {
      bullet: 'bg-purple-500',
      headerBg: 'bg-purple-100/50 border-purple-200',
      textHeader: 'text-purple-800',
      textCount: 'text-purple-700 border-purple-200',
      checkboxColor: 'text-purple-600 focus:ring-purple-200',
      dragBg: 'bg-purple-50 border-purple-300 ring-4 ring-purple-100',
      itemBorder: 'border-purple-350 bg-purple-50/20',
      actions: [
        { label: 'T-B', isToxic: true, isBully: true },
        { label: 'T-NB', isToxic: true, isBully: false },
        { label: 'Aman', isToxic: false, isBully: false }
      ]
    },
    emerald: {
      bullet: 'bg-emerald-500',
      headerBg: 'bg-emerald-100/50 border-emerald-200',
      textHeader: 'text-emerald-800',
      textCount: 'text-emerald-700 border-emerald-200',
      checkboxColor: 'text-emerald-600 focus:ring-emerald-200',
      dragBg: 'bg-emerald-50 border-emerald-300 ring-4 ring-emerald-100',
      itemBorder: 'border-emerald-350 bg-emerald-50/20',
      actions: [
        { label: 'T-B', isToxic: true, isBully: true },
        { label: 'T-NB', isToxic: true, isBully: false },
        { label: 'NT-B', isToxic: false, isBully: true }
      ]
    }
  }[theme];

  const allSelected = items.length > 0 && items.every(item => selectedItems.includes(item.text));
  const currentQuadCode = {
    rose: 'tb',
    amber: 'tnb',
    purple: 'ntb',
    emerald: 'ntnb'
  }[theme];

  return (
    <div 
      className="flex flex-col gap-3"
      style={{
        zIndex: isOver ? 10 : 1,
        position: 'relative'
      }}
    >
      <div className={`p-3 rounded-xl flex flex-col gap-1.5 ${config.headerBg}`}>
        <div className="flex justify-between items-center w-full">
          <h3 className={`text-xs font-black flex items-center gap-1 ${config.textHeader}`}>
            <span className={`w-2 h-2 rounded-full ${config.bullet}`} /> {title}
          </h3>
          <span className={`text-xxs font-bold bg-white border px-1.5 py-0.5 rounded ${config.textCount}`}>
            {items.length} item
          </span>
        </div>
        {items.length > 0 && (
          <div className="flex items-center gap-1.5 mt-0.5 border-t border-gray-250 pt-1.5">
            <input
              type="checkbox"
              checked={allSelected}
              onChange={(e) => onSelectAll(e.target.checked)}
              className={`w-3.5 h-3.5 rounded border-gray-300 cursor-pointer ${config.checkboxColor}`}
            />
            <span className={`text-[10px] font-bold ${config.textHeader}`}>Pilih Semua</span>
          </div>
        )}
      </div>
      
      <div 
        className={`bg-gray-50 border border-gray-100 rounded-xl p-3 flex flex-col gap-2.5 min-h-[320px] max-h-[350px] custom-scrollbar transition-all duration-250 ${isOver ? `${config.dragBg} border-dashed` : ""}`}
        style={{
          overflow: 'auto',
          position: 'relative'
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setIsOver(true);
        }}
        onDragLeave={() => setIsOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsOver(false);
          const text = e.dataTransfer.getData('text/plain');
          if (text) {
            onDrop(text);
          }
        }}
        data-quadrant={currentQuadCode}
      >
        {isLoading ? (
          <p className="text-xxs text-gray-400 italic text-center py-4">Memuat data...</p>
        ) : items.length === 0 ? (
          <p className="text-xxs text-gray-400 italic text-center py-4">Kuadran kosong / Tarik ke sini</p>
        ) : (
          items.map((item) => (
            <QuadrantCard
              key={item.text}
              item={item}
              theme={theme}
              selectedItems={selectedItems}
              config={config}
              onSelectItem={onSelectItem}
              onReallocate={onReallocate}
            />
          ))
        )}
      </div>
    </div>
  );
}
