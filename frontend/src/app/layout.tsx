import type { Metadata } from "next";
import "./globals.css";
import { BookOpen, Search, Settings, UserCircle } from "lucide-react";
import Link from "next/link";

export const metadata: Metadata = {
  title: "RepoSense",
  description: "Developer intelligence tool",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased flex flex-col min-h-screen bg-gh-bg-inset">
        <header className="flex items-center justify-between px-4 py-3 bg-[#24292f] text-white">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-2 text-white hover:text-gray-300">
              <BookOpen size={24} />
              <span className="font-semibold text-lg">RepoSense</span>
            </Link>
            
            <div className="hidden md:flex items-center relative">
              <div className="absolute left-2 text-gray-400">
                <Search size={14} />
              </div>
              <input 
                type="text" 
                placeholder="Type / to search" 
                className="bg-[#24292f] border border-gray-500 rounded-md py-1 pl-8 pr-3 text-sm focus:bg-white focus:text-black w-64 transition-colors"
              />
            </div>
            
            <nav className="hidden md:flex gap-4 text-sm font-semibold ml-2">
              <Link href="/" className="hover:text-gray-300">Pull requests</Link>
              <Link href="/" className="hover:text-gray-300">Issues</Link>
              <Link href="/" className="hover:text-gray-300">Codespaces</Link>
              <Link href="/" className="hover:text-gray-300">Marketplace</Link>
              <Link href="/" className="hover:text-gray-300">Explore</Link>
            </nav>
          </div>
          
          <div className="flex items-center gap-3">
            <Settings size={20} className="text-gray-300 cursor-pointer hover:text-white" />
            <UserCircle size={24} className="text-gray-300 cursor-pointer hover:text-white" />
          </div>
        </header>
        
        <main className="flex-1 flex flex-col">
          {children}
        </main>
      </body>
    </html>
  );
}
