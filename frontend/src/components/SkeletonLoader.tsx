import React from 'react';

export function SkeletonComment() {
  return (
    <div className="animate-pulse flex gap-3 p-4 bg-gray-55/40 dark:bg-white/5 border border-gray-100 dark:border-gray-800 rounded-xl">
      <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full shrink-0" />
      <div className="flex-1 flex flex-col gap-2 min-w-0">
        <div className="w-1/4 h-3 bg-gray-200 dark:bg-gray-700 rounded" />
        <div className="w-3/4 h-4 bg-gray-200 dark:bg-gray-700 rounded" />
      </div>
    </div>
  );
}

export function SkeletonTableRow() {
  return (
    <tr className="animate-pulse">
      <td className="px-6 py-4">
        <div className="h-4 bg-gray-200 dark:bg-gray-750 rounded w-5/6" />
      </td>
      <td className="px-6 py-4">
        <div className="h-5 bg-gray-200 dark:bg-gray-750 rounded w-16" />
      </td>
      <td className="px-6 py-4">
        <div className="h-4 bg-gray-200 dark:bg-gray-750 rounded w-8" />
      </td>
      <td className="px-6 py-4">
        <div className="h-4 bg-gray-200 dark:bg-gray-750 rounded w-8" />
      </td>
      <td className="px-6 py-4 text-right">
        <div className="flex justify-end gap-1.5">
          <div className="w-10 h-6 bg-gray-200 dark:bg-gray-750 rounded" />
          <div className="w-10 h-6 bg-gray-200 dark:bg-gray-750 rounded" />
          <div className="w-10 h-6 bg-gray-200 dark:bg-gray-750 rounded" />
        </div>
      </td>
    </tr>
  );
}

export function SkeletonStatsWidget() {
  return (
    <div className="animate-pulse premium-card p-5 flex flex-col items-center justify-center text-center">
      <div className="w-24 h-3 bg-gray-200 dark:bg-gray-700 rounded mb-2.5" />
      <div className="w-16 h-8 bg-gray-200 dark:bg-gray-700 rounded" />
    </div>
  );
}

export function SkeletonFreqWidget() {
  return (
    <div className="animate-pulse premium-card p-5 flex flex-col gap-3">
      <div className="w-1/3 h-3 bg-gray-200 dark:bg-gray-700 rounded" />
      <div className="flex flex-col gap-3.5 mt-1.5">
        {[1, 2, 3].map((n) => (
          <div key={n} className="flex flex-col gap-2">
            <div className="flex justify-between">
              <div className="w-16 h-3 bg-gray-200 dark:bg-gray-700 rounded" />
              <div className="w-6 h-3 bg-gray-200 dark:bg-gray-700 rounded" />
            </div>
            <div className="w-full h-1 bg-gray-200 dark:bg-gray-700 rounded-full" />
          </div>
        ))}
      </div>
    </div>
  );
}
