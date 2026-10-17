"use client";

import { Header } from "@/components/Header";
import { UploadArea } from "@/components/UploadArea";
import { submitAndPoll, triggerDownload } from "@/lib/apiClient";

export default function ExcelToPDFPage() {
  const handleProcess = async (files: File[], onStatus: (msg: string) => void) => {
    const formData = new FormData();
    formData.append("file", files[0]);

    const { filename, downloadUrl } = await submitAndPoll("/excel-to-pdf", formData, onStatus);
    triggerDownload(downloadUrl, filename);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center">
      <Header />
      <main className="flex-1 w-full max-w-3xl px-4 md:px-8 py-16 flex flex-col items-center">
        <h1 className="text-4xl md:text-5xl font-bold text-center text-gray-900 mb-6">
          Excel to PDF
        </h1>
        <p className="text-xl text-gray-500 text-center mb-12 max-w-2xl">
          Make EXCEL spreadsheets easy to read by converting them to PDF.
        </p>
        <UploadArea
          onProcess={handleProcess}
          title="Select Excel file"
          buttonText="Convert to PDF"
          accept=".xls,.xlsx"
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
