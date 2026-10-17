"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useSession, signOut } from "next-auth/react";
import { FileText, Menu, X, User, LogOut, ChevronDown, Sparkles } from "lucide-react";
import { AuthModal } from "./AuthModal";

export function Header() {
  const { data: session, status } = useSession();
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "signup">("login");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);

  const openAuth = (mode: "login" | "signup") => {
    setAuthMode(mode);
    setAuthModalOpen(true);
    setMobileMenuOpen(false);
  };

  const handleSignOut = async () => {
    setUserDropdownOpen(false);
    setMobileMenuOpen(false);
    await signOut({ redirect: false });
  };

  const getInitials = (name?: string | null, email?: string | null) => {
    if (name) {
      const parts = name.trim().split(" ");
      if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
      return name.slice(0, 2).toUpperCase();
    }
    if (email) return email.slice(0, 2).toUpperCase();
    return "U";
  };

  return (
    <>
      <header className="sticky top-0 z-40 w-full bg-white border-b border-gray-100 shadow-xs">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-9 h-9 bg-primary rounded-xl flex items-center justify-center text-white transition-transform group-hover:scale-105 shadow-sm shadow-primary/30">
              <FileText size={22} strokeWidth={2.5} />
            </div>
            <span className="text-2xl font-black tracking-tight text-gray-900 group-hover:text-primary transition-colors">
              iLovePDF<span className="text-gray-500 font-bold ml-1 text-xl">Tools</span>
            </span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-8">
            <Link
              href="/"
              className="text-sm font-bold text-gray-700 hover:text-primary transition-colors"
            >
              MERGE PDF
            </Link>
            <Link
              href="/split-pdf"
              className="text-sm font-bold text-gray-700 hover:text-primary transition-colors"
            >
              SPLIT PDF
            </Link>
            <Link
              href="/compress-pdf"
              className="text-sm font-bold text-gray-700 hover:text-primary transition-colors"
            >
              COMPRESS PDF
            </Link>
            <Link
              href="/"
              className="text-sm font-bold text-gray-700 hover:text-primary transition-colors flex items-center gap-1"
            >
              <span>ALL PDF TOOLS</span>
            </Link>
          </nav>

          {/* Desktop Auth Section */}
          <div className="hidden md:flex items-center gap-4">
            {status === "loading" ? (
              <div className="h-9 w-28 bg-gray-100 animate-pulse rounded-full" />
            ) : session?.user ? (
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setUserDropdownOpen(!userDropdownOpen)}
                  className="flex items-center gap-2.5 p-1.5 pr-3 rounded-full hover:bg-gray-100 transition-colors border border-gray-200 cursor-pointer"
                >
                  <div className="w-8 h-8 rounded-full bg-primary text-white font-bold text-xs flex items-center justify-center shadow-xs">
                    {getInitials(session.user.name, session.user.email)}
                  </div>
                  <div className="text-left hidden lg:block">
                    <p className="text-xs font-bold text-gray-800 leading-tight">
                      {session.user.name || "Member"}
                    </p>
                    <p className="text-[10px] text-gray-400 leading-tight truncate max-w-[120px]">
                      {session.user.email}
                    </p>
                  </div>
                  <ChevronDown size={14} className="text-gray-400" />
                </button>

                {/* User Dropdown Menu */}
                {userDropdownOpen && (
                  <div
                    className="absolute right-0 mt-2 w-56 bg-white rounded-2xl shadow-xl border border-gray-100 py-2 z-50 animate-in fade-in slide-in-from-top-1 duration-150"
                    onMouseLeave={() => setUserDropdownOpen(false)}
                  >
                    <div className="px-4 py-3 border-b border-gray-100">
                      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                        Signed in as
                      </p>
                      <p className="text-sm font-bold text-gray-900 truncate mt-0.5">
                        {session.user.name || session.user.email}
                      </p>
                      <div className="mt-1 flex items-center gap-1.5 text-xs text-primary font-medium">
                        <Sparkles size={12} />
                        <span>Free Plan Active</span>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={handleSignOut}
                      className="w-full px-4 py-2.5 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2 transition-colors cursor-pointer font-medium"
                    >
                      <LogOut size={16} />
                      <span>Log out</span>
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => openAuth("login")}
                  className="text-sm font-bold text-gray-700 hover:text-primary transition-colors cursor-pointer px-3 py-2 rounded-lg hover:bg-gray-50"
                >
                  Login
                </button>
                <button
                  type="button"
                  onClick={() => openAuth("signup")}
                  className="bg-primary hover:bg-primary/95 text-white rounded-full font-bold px-6 py-2 transition-transform active:scale-95 cursor-pointer shadow-sm shadow-primary/25"
                >
                  Sign up
                </button>
              </>
            )}
          </div>

          {/* Mobile Menu Toggle Button */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-gray-600 hover:text-primary rounded-lg hover:bg-gray-100 transition-colors"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-gray-100 bg-white px-4 py-6 space-y-4 animate-in fade-in slide-in-from-top-2 duration-150">
            <nav className="flex flex-col gap-3">
              <Link
                href="/"
                onClick={() => setMobileMenuOpen(false)}
                className="text-sm font-bold text-gray-700 hover:text-primary py-2"
              >
                MERGE PDF
              </Link>
              <Link
                href="/split-pdf"
                onClick={() => setMobileMenuOpen(false)}
                className="text-sm font-bold text-gray-700 hover:text-primary py-2"
              >
                SPLIT PDF
              </Link>
              <Link
                href="/compress-pdf"
                onClick={() => setMobileMenuOpen(false)}
                className="text-sm font-bold text-gray-700 hover:text-primary py-2"
              >
                COMPRESS PDF
              </Link>
              <Link
                href="/"
                onClick={() => setMobileMenuOpen(false)}
                className="text-sm font-bold text-gray-700 hover:text-primary py-2"
              >
                ALL PDF TOOLS
              </Link>
            </nav>

            <div className="pt-4 border-t border-gray-100 flex flex-col gap-2">
              {session?.user ? (
                <div className="space-y-3">
                  <div className="flex items-center gap-3 p-2 bg-gray-50 rounded-xl">
                    <div className="w-10 h-10 rounded-full bg-primary text-white font-bold text-sm flex items-center justify-center">
                      {getInitials(session.user.name, session.user.email)}
                    </div>
                    <div className="truncate">
                      <p className="text-sm font-bold text-gray-900">
                        {session.user.name || "User"}
                      </p>
                      <p className="text-xs text-gray-500 truncate">{session.user.email}</p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={handleSignOut}
                    className="w-full py-2.5 px-4 bg-red-50 text-red-600 font-bold rounded-xl text-sm flex items-center justify-center gap-2 hover:bg-red-100 transition-colors"
                  >
                    <LogOut size={16} />
                    <span>Log out</span>
                  </button>
                </div>
              ) : (
                <>
                  <button
                    type="button"
                    onClick={() => openAuth("login")}
                    className="w-full py-2.5 text-center text-sm font-bold text-gray-700 border border-gray-200 rounded-xl hover:bg-gray-50 transition"
                  >
                    Login
                  </button>
                  <button
                    type="button"
                    onClick={() => openAuth("signup")}
                    className="w-full py-2.5 text-center text-sm font-bold text-white bg-primary hover:bg-primary/95 rounded-xl shadow-sm transition"
                  >
                    Sign up
                  </button>
                </>
              )}
            </div>
          </div>
        )}
      </header>

      {/* Inline Auth Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        initialMode={authMode}
      />
    </>
  );
}
