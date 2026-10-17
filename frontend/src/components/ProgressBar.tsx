"use client";

import React, { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

interface ProgressBarProps {
  statusMsg: string;
}

export function ProgressBar({ statusMsg }: ProgressBarProps) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const startTime = Date.now();
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center w-full max-w-sm">
      <Loader2 className="w-16 h-16 text-primary animate-spin mb-4" />
      <div className="flex justify-between w-full mb-2 px-2">
        <span className="text-sm font-medium text-gray-700">{statusMsg}</span>
        <span className="text-sm font-medium text-gray-500">{elapsed}s</span>
      </div>
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes indeterminate {
          0% { left: -35%; right: 100%; }
          60% { left: 100%; right: -90%; }
          100% { left: 100%; right: -90%; }
        }
        .animate-indeterminate {
          animation: indeterminate 2s infinite ease-in-out;
        }
      `}} />
      <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden relative">
        <div className="bg-primary h-2.5 rounded-full absolute w-1/3 animate-indeterminate"></div>
      </div>
    </div>
  );
}
