import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Header } from "@/components/Header";
import { 
  FilePlus, 
  SplitSquareHorizontal, 
  Minimize, 
  FileText, 
  Image as ImageIcon,
  FileImage,
  Lock,
  Unlock,
  Type,
  FileSpreadsheet,
  RotateCw,
  Droplets,
  FileMinus,
  FileSymlink,
  Grid
} from "lucide-react";

const tools = [
  {
    title: "Merge PDF",
    description: "Combine PDFs in the order you want with the easiest PDF merger available.",
    icon: <FilePlus className="w-10 h-10 text-primary mb-4" />,
    href: "/merge-pdf",
  },
  {
    title: "Split PDF",
    description: "Separate one page or a whole set for easy conversion into independent PDF files.",
    icon: <SplitSquareHorizontal className="w-10 h-10 text-primary mb-4" />,
    href: "/split-pdf",
  },
  {
    title: "Compress PDF",
    description: "Reduce file size while optimizing for maximal PDF quality.",
    icon: <Minimize className="w-10 h-10 text-primary mb-4" />,
    href: "/compress-pdf",
  },
  {
    title: "PDF to Word",
    description: "Easily convert your PDF files into easy to edit DOC and DOCX documents.",
    icon: <FileText className="w-10 h-10 text-primary mb-4" />,
    href: "/pdf-to-word",
  },
  {
    title: "Word to PDF",
    description: "Make DOC and DOCX files easy to read by converting them to PDF.",
    icon: <FileText className="w-10 h-10 text-primary mb-4" />,
    href: "/word-to-pdf",
  },
  {
    title: "PDF to JPG",
    description: "Convert each PDF page into a JPG or extract all images contained in a PDF.",
    icon: <ImageIcon className="w-10 h-10 text-primary mb-4" />,
    href: "/pdf-to-jpg",
  },
  {
    title: "JPG to PDF",
    description: "Convert JPG images to PDF in seconds. Easily adjust orientation and margins.",
    icon: <FileImage className="w-10 h-10 text-primary mb-4" />,
    href: "/jpg-to-pdf",
  },
  {
    title: "Protect PDF",
    description: "Encrypt your PDF with a password to keep sensitive data confidential.",
    icon: <Lock className="w-10 h-10 text-primary mb-4" />,
    href: "/protect-pdf",
  },
  {
    title: "Unlock PDF",
    description: "Remove PDF password security, giving you the freedom to use your PDFs as you want.",
    icon: <Unlock className="w-10 h-10 text-primary mb-4" />,
    href: "/unlock-pdf",
  },
  {
    title: "Add Page Numbers",
    description: "Add page numbers into PDFs with ease. Choose your positions, dimensions, typography.",
    icon: <Type className="w-10 h-10 text-primary mb-4" />,
    href: "/add-page-numbers",
  },
  {
    title: "PDF to Excel",
    description: "Convert PDF data to EXCEL spreadsheets. Solid PDF to EXCEL converter.",
    icon: <FileSpreadsheet className="w-10 h-10 text-primary mb-4" />,
    href: "/pdf-to-excel",
  },
  {
    title: "Excel to PDF",
    description: "Make EXCEL spreadsheets easy to read by converting them to PDF.",
    icon: <FileSpreadsheet className="w-10 h-10 text-primary mb-4" />,
    href: "/excel-to-pdf",
  },
  {
    title: "Rotate PDF",
    description: "Rotate your PDFs the way you need them. You can even rotate multiple PDFs at once!",
    icon: <RotateCw className="w-10 h-10 text-primary mb-4" />,
    href: "/rotate-pdf",
  },
  {
    title: "Watermark PDF",
    description: "Stamp an image or text over your PDF in seconds. Choose the typography, transparency and position.",
    icon: <Droplets className="w-10 h-10 text-primary mb-4" />,
    href: "/watermark-pdf",
  },
  {
    title: "Remove pages",
    description: "Remove some pages from your document. Delete PDF pages in a blink.",
    icon: <FileMinus className="w-10 h-10 text-primary mb-4" />,
    href: "/remove-pages",
  },
  {
    title: "Extract pages",
    description: "Get a new document containing only the desired pages. Leave the rest behind.",
    icon: <FileSymlink className="w-10 h-10 text-primary mb-4" />,
    href: "/extract-pages",
  },
  {
    title: "Organize PDF",
    description: "Sort pages of your PDF file however you like. Delete PDF pages or add PDF pages to your document at your convenience.",
    icon: <Grid className="w-10 h-10 text-primary mb-4" />,
    href: "/organize-pdf",
  }
];

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center">
      <Header />

      <main className="flex-1 w-full px-4 md:px-8 py-16 flex flex-col items-center">
        <h1 className="text-4xl md:text-5xl font-bold text-center text-gray-900 mb-6">
          Every tool you need to work with PDFs in one place
        </h1>
        <p className="text-xl text-gray-600 text-center mb-16 max-w-3xl">
          Every tool you need to use PDFs, at your fingertips. All are 100% FREE and easy to use! Merge, split, compress, convert, rotate, unlock and watermark PDFs with just a few clicks.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 w-full max-w-[1400px]">
          {tools.map((tool, index) => (
            <Link key={index} href={tool.href} className="group block h-full">
              <Card className="h-full border border-gray-100 rounded-sm shadow-[0_1px_4px_rgba(0,0,0,0.08)] hover:shadow-[0_8px_24px_rgba(0,0,0,0.12)] transition-all duration-300 bg-white group-hover:-translate-y-1">
                <CardContent className="p-6 flex flex-col items-start text-left">
                  {tool.icon}
                  <CardTitle className="mb-2 text-xl font-bold text-gray-800 transition-colors">
                    {tool.title}
                  </CardTitle>
                  <CardDescription className="text-sm text-gray-500 leading-relaxed">
                    {tool.description}
                  </CardDescription>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </main>

      <footer className="w-full bg-white border-t py-8 mt-12 text-center text-gray-500 text-sm">
        &copy; {new Date().getFullYear()} iLovePDF Tools
      </footer>
    </div>
  );
}
