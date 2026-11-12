import React, { useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  Mic,
  CloudRain,
  TestTube2,
  Sprout,
  CalendarCheck,
  Bug,
  FlaskConical,
  TrendingUp,
  Apple,
  Store,
  Calculator,
  Landmark,
  UserCircle,
  LogOut,
  Menu,
  X,
  Globe,
} from "lucide-react";
import { BrandLogo } from "@/components/common/BrandLogo";
import { useAuth } from "@/context/AuthContext";
import { SUPPORTED_LANGUAGES, useLanguage } from "@/context/LanguageContext";
import type { LanguageCode } from "@/types";

interface NavItem {
  to: string;
  key: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  { to: "/dashboard", key: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/voice", key: "voice", label: "Voice Assistant", icon: Mic },
  { to: "/weather", key: "weather", label: "Weather & Flood", icon: CloudRain },
  { to: "/soil", key: "soil", label: "Soil Health", icon: TestTube2 },
  { to: "/crops", key: "crops", label: "Crop Advice", icon: Sprout },
  { to: "/growth", key: "growth", label: "Crop Growth", icon: CalendarCheck },
  { to: "/pest-detection", key: "pests", label: "Pest & Disease", icon: Bug },
  { to: "/fertilizer", key: "fertilizer", label: "Fertilizer", icon: FlaskConical },
  { to: "/yield", key: "yield", label: "Yield & Harvest", icon: TrendingUp },
  { to: "/nutrition", key: "nutrition", label: "Nutrition", icon: Apple },
  { to: "/mandi", key: "mandi", label: "Mandi Prices", icon: Store },
  { to: "/profit", key: "profit", label: "Profit Calculator", icon: Calculator },
  { to: "/schemes", key: "schemes", label: "Govt Schemes", icon: Landmark },
  { to: "/profile", key: "profile", label: "Profile & Settings", icon: UserCircle },
];

export const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { farmer, logout } = useAuth();
  const { language, setLanguage, t } = useLanguage();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  return (
    <div className="min-h-screen bg-cream text-ink flex flex-col lg:flex-row">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex lg:w-64 lg:flex-col lg:fixed lg:inset-y-0 bg-white border-r border-[#176B35]/10">
        <div className="p-5 border-b border-[#176B35]/10">
          <Link to="/dashboard" className="block">
            <BrandLogo size="md" />
          </Link>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isVoice = item.to === "/voice";
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-forest text-white shadow-sm"
                      : isVoice
                      ? "bg-mint/70 text-deep hover:bg-mint"
                      : "text-ink/80 hover:bg-mint/50 hover:text-deep"
                  }`
                }
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span className="truncate">{t(item.key, item.label)}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="p-4 border-t border-[#176B35]/10 space-y-3">
          {farmer && (
            <div className="rounded-xl bg-mint/60 px-3 py-2.5">
              <p className="text-xs font-semibold text-deep truncate">{farmer.full_name}</p>
              <p className="text-[11px] text-muted truncate">
                {farmer.village || farmer.district}, {farmer.state}
              </p>
            </div>
          )}
          <button
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 rounded-xl border border-[#202820]/15 px-3 py-2 text-xs font-semibold text-muted hover:text-danger hover:border-danger/40 transition-colors"
          >
            <LogOut className="h-3.5 w-3.5" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 lg:pl-64 flex flex-col min-h-screen">
        {/* Top Bar */}
        <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-sm border-b border-[#176B35]/10 px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="lg:hidden p-2 rounded-xl border border-[#176B35]/15 text-deep hover:bg-mint"
              aria-label="Open navigation menu"
            >
              <Menu className="h-5 w-5" />
            </button>
            <Link to="/dashboard" className="lg:hidden">
              <BrandLogo size="sm" />
            </Link>
            <span className="hidden lg:inline text-xs font-medium text-muted">
              {t("tagline", "Your Smart Farming Companion")}
            </span>
          </div>

          <div className="flex items-center gap-2.5">
            <div className="inline-flex items-center gap-1.5 rounded-xl border border-[#176B35]/20 bg-cream px-2.5 py-1.5">
              <Globe className="h-3.5 w-3.5 text-forest" />
              <select
                aria-label="Select interface language"
                value={language}
                onChange={(e) => setLanguage(e.target.value as LanguageCode)}
                className="bg-transparent text-xs font-semibold text-deep focus:outline-none"
              >
                {SUPPORTED_LANGUAGES.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.nativeName} ({lang.name})
                  </option>
                ))}
              </select>
            </div>

            <Link
              to="/voice"
              className="hidden sm:inline-flex items-center gap-1.5 rounded-xl bg-forest px-3.5 py-2 text-xs font-semibold text-white hover:bg-deep transition-colors"
            >
              <Mic className="h-3.5 w-3.5" />
              <span>{t("voice", "Ask Raitha Mitra")}</span>
            </Link>
          </div>
        </header>

        {/* Page Body */}
        <main className="flex-1 px-4 sm:px-6 lg:px-8 py-6 pb-24 lg:pb-8 max-w-7xl w-full mx-auto">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
          >
            {children}
          </motion.div>
        </main>

        {/* Mobile Bottom Quick Navigation */}
        <nav className="lg:hidden fixed bottom-0 inset-x-0 z-30 bg-white border-t border-[#176B35]/10 px-2 py-1.5 flex items-center justify-around">
          {[
            { to: "/dashboard", icon: LayoutDashboard, label: "Home" },
            { to: "/weather", icon: CloudRain, label: "Weather" },
            { to: "/voice", icon: Mic, label: "Voice", highlight: true },
            { to: "/mandi", icon: Store, label: "Mandi" },
            { to: "/soil", icon: TestTube2, label: "Soil" },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex flex-col items-center gap-0.5 rounded-xl px-3 py-1.5 text-[11px] font-medium ${
                    item.highlight
                      ? "bg-forest text-white shadow-sm"
                      : isActive
                      ? "text-forest font-semibold"
                      : "text-muted"
                  }`
                }
              >
                <Icon className="h-4 w-4" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div
            className="fixed inset-0 bg-ink/40"
            onClick={() => setMobileMenuOpen(false)}
          />
          <div className="relative w-72 max-w-[85vw] bg-white h-full flex flex-col shadow-xl z-10">
            <div className="p-4 border-b border-[#176B35]/10 flex items-center justify-between">
              <BrandLogo size="sm" />
              <button
                onClick={() => setMobileMenuOpen(false)}
                className="p-1.5 rounded-lg text-muted hover:bg-mint"
                aria-label="Close navigation menu"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <nav className="flex-1 overflow-y-auto p-3 space-y-1">
              {NAV_ITEMS.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    onClick={() => setMobileMenuOpen(false)}
                    className={({ isActive }) =>
                      `flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium ${
                        isActive ? "bg-forest text-white" : "text-ink/85 hover:bg-mint/60"
                      }`
                    }
                  >
                    <Icon className="h-4 w-4" />
                    <span>{t(item.key, item.label)}</span>
                  </NavLink>
                );
              })}
            </nav>
            <div className="p-4 border-t border-[#176B35]/10">
              <button
                onClick={() => {
                  setMobileMenuOpen(false);
                  logout();
                }}
                className="w-full rm-btn-secondary text-xs"
              >
                <LogOut className="h-3.5 w-3.5" />
                Sign Out
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
