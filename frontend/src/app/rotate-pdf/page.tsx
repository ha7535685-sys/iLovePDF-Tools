"use client";

import { Header } from "@/components/Header";
import { UploadArea } from "@/components/UploadArea";
import { useState } from "react";
import { Label } from "@/components/ui/label";
import { submitAndPoll, triggerDownload } from "@/lib/apiClient";

export default function RotatePDFPage() {
  const [rotation, setRotation] = useState("90");

  const handleProcess = async (files: File[], onStatus: (msg: string) => void) => {
    const formData = new FormData();
    formData.append("file", files[0]);
    formData.append("rotation", rotation);

    const { filename, downloadUrl } = await submitAndPoll("/rotate-pdf", formData, onStatus);
    triggerDownload(downloadUrl, filename);
  };

  return (
    <div className="min-h-screen bg-[#FDFBF9] flex flex-col items-center">
      <Header />
      <main className="flex-1 w-full max-w-3xl px-4 md:px-8 py-16 flex flex-col items-center">
        <h1 className="text-4xl md:text-5xl font-bold text-center text-gray-900 mb-6">
          Rotate PDF
        </h1>
        <p className="text-xl text-gray-600 text-center mb-12 max-w-2xl">
          Rotate your PDFs the way you need them.
        </p>
        <div className="w-full max-w-md mb-6 px-4">
          <div className="bg-white p-6 rounded-xl shadow-sm border mb-4">
            <Label htmlFor="rotation" className="text-lg font-semibold mb-2 block">Rotation Angle</Label>
            <select
              id="rotation"
              value={rotation}
              onChange={(e) => setRotation(e.target.value)}
              className="w-full border rounded-md p-3 mt-2 bg-gray-50 focus:ring-2 focus:ring-primary focus:border-transparent transition-all outline-none"
            >
              <option value="90">90 Degrees Clockwise</option>
              <option value="180">180 Degrees Clockwise</option>
              <option value="270">90 Degrees Counter-Clockwise</option>
            </select>
          </div>
        </div>
        <UploadArea
          onProcess={handleProcess}
          title="Select PDF file"
          buttonText="Rotate PDF"
          accept=".pdf"
          multiple={false}
          maxFiles={1}
        />
      </main>
      <footer className="w-full bg-white border-t py-8 mt-12 text-center text-gray-500 text-sm">
        &copy; {new Date().getFullYear()} iLovePDF Tools
      </footer>
    </div>
  );
}
