import { Search } from 'lucide-react';

export function EmptyState() {
  return (
    <div className="premium-card p-8 flex flex-col items-center justify-center text-center min-h-[400px]">
      <div className="w-24 h-24 rounded-full bg-gray-50 flex items-center justify-center border border-gray-100 mb-4 text-gray-400">
        <Search className="w-10 h-10" />
      </div>
      <h3 className="text-sm font-bold text-gray-800 mb-1">Menunggu Input Analisis</h3>
      <p className="text-xs text-gray-400 max-w-xs leading-relaxed">
        Masukkan kalimat atau teks di panel kiri, pilih model dan klik tombol Analisis Sekarang.
      </p>
    </div>
  );
}
