import React from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Mic,
  CloudRain,
  TestTube2,
  Sprout,
  Bug,
  Store,
  Calculator,
  Landmark,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
} from "lucide-react";
import { BrandLogo } from "@/components/common/BrandLogo";
import { SUPPORTED_LANGUAGES } from "@/context/LanguageContext";
import { useAuth } from "@/context/AuthContext";

const FEATURES = [
  {
    icon: Mic,
    title: "Multilingual Voice Companion",
    desc: "Speak naturally in Kannada, Hindi, Telugu, Tamil, Marathi, or English with real-time interruption support grounded in your farm profile.",
  },
  {
    icon: TestTube2,
    title: "Soil Health & Lab OCR",
    desc: "Upload Soil Health Cards or lab PDFs/photos with mandatory review-and-correct, or inspect clearly labelled dataset estimates.",
  },
  {
    icon: CloudRain,
    title: "IMD Warnings & Flood Watch",
    desc: "Official IMD weather warning integration, forecast fallback, and honest CWC flood feed status with freshness timestamps.",
  },
  {
    icon: Sprout,
    title: "Crop & Stage Guidance",
    desc: "Tailored recommendations across cereals, pulses, vegetables, and fruits plus day-by-day irrigation and nutrient tasks.",
  },
  {
    icon: Bug,
    title: "Pest & Disease Triage",
    desc: "Upload crop leaf photos for symptom analysis, organic and chemical care options, and safety precautions via verified adapters.",
  },
  {
    icon: Store,
    title: "Mandi Prices & Profit",
    desc: "Latest available daily AGMARKNET/CEDA prices, cross-market comparisons, and Low/Expected/Optimistic profit scenarios.",
  },
  {
    icon: Calculator,
    title: "Yield, Nutrition & Fertilizer",
    desc: "Modular yield & maturity harvest windows, NPK plans by deficiency, and ICMR-NIN/USDA/PubMed nutrition utilization.",
  },
  {
    icon: Landmark,
    title: "Verified Govt Schemes",
    desc: "Filter central and state schemes by landholding, category, and crop with verified official portal URLs and checklists.",
  },
];

export const LandingPage: React.FC = () => {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-cream text-ink flex flex-col">
      {/* Header */}
      <header className="bg-white/95 border-b border-[#176B35]/10 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
          <Link to="/">
            <BrandLogo size="sm" />
          </Link>
          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-muted">
            <a href="#features" className="hover:text-forest transition-colors">
              Features
            </a>
            <a href="#how-it-works" className="hover:text-forest transition-colors">
              How It Works
            </a>
            <a href="#languages" className="hover:text-forest transition-colors">
              Languages
            </a>
          </nav>
          <div className="flex items-center gap-2.5">
            {isAuthenticated ? (
              <Link to="/dashboard" className="rm-btn-primary">
                Open Dashboard
                <ArrowRight className="h-4 w-4" />
              </Link>
            ) : (
              <>
                <Link to="/auth" className="rm-btn-secondary hidden sm:inline-flex">
                  Sign In
                </Link>
                <Link to="/auth?mode=register" className="rm-btn-primary">
                  Get Started
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative py-12 sm:py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto text-center space-y-6">
          <div className="flex justify-center">
            <BrandLogo size="lg" animateEntrance />
          </div>

          <div className="inline-flex items-center gap-2 rounded-full bg-mint px-4 py-1.5 text-xs font-semibold text-forest border border-leaf/25">
            <ShieldCheck className="h-4 w-4" />
            Transparent, farmer-first agricultural intelligence for India
          </div>

          <motion.h1
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-deep leading-tight"
          >
            Your Farm. Your Future. Our Intelligence.
          </motion.h1>

          <p className="text-base sm:text-lg text-muted max-w-2xl mx-auto leading-relaxed">
            Raitha Mitra brings voice-first multilingual guidance, Soil Health Card analysis,
            weather alerts, crop stage tracking, mandi prices, and farm profit planning into one
            calm, reliable workspace built for mobile and desktop.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
            <Link
              to={isAuthenticated ? "/dashboard" : "/auth?mode=register"}
              className="rm-btn-primary w-full sm:w-auto px-7 py-3.5 text-base"
            >
              Get Started
              <ArrowRight className="h-4 w-4" />
            </Link>
            <a
              href="#features"
              className="rm-btn-secondary w-full sm:w-auto px-7 py-3.5 text-base"
            >
              Explore Features
            </a>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-14 px-4 sm:px-6 lg:px-8 bg-white border-y border-[#176B35]/10">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-10">
            <h2 className="text-2xl sm:text-3xl font-bold text-deep">
              Every Stage of the Season Covered
            </h2>
            <p className="text-sm sm:text-base text-muted mt-2">
              Designed with honest source attribution, strict per-farmer privacy, and clear estimates.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {FEATURES.map((feat, idx) => {
              const Icon = feat.icon;
              return (
                <motion.div
                  key={feat.title}
                  initial={{ opacity: 0, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.35, delay: idx * 0.04 }}
                  className="rm-card p-5 flex flex-col gap-3 hover:border-forest/30 transition-colors"
                >
                  <div className="h-10 w-10 rounded-xl bg-mint flex items-center justify-center text-forest">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="text-base font-bold text-ink">{feat.title}</h3>
                  <p className="text-sm text-muted leading-relaxed">{feat.desc}</p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-14 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-deep text-center mb-10">
            How Raitha Mitra Works
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                step: "01",
                title: "Set Up Your Farm Profile",
                body: "Enter your village, district, crops, and preferred language. GPS coordinates are strictly opt-in—manual location always works.",
              },
              {
                step: "02",
                title: "Add Soil & Crop Context",
                body: "Upload your Soil Health Card to review extracted values, log active sown crops, and inspect weather & mandi availability.",
              },
              {
                step: "03",
                title: "Ask by Voice in Your Language",
                body: "Tap the mic and ask questions in Kannada, Hindi, Telugu, or English. Raitha Mitra answers using your real farm context.",
              },
            ].map((item) => (
              <div key={item.step} className="rm-card p-6 space-y-3">
                <span className="inline-block rounded-lg bg-mint px-3 py-1 text-xs font-bold text-forest">
                  STEP {item.step}
                </span>
                <h3 className="text-lg font-bold text-ink">{item.title}</h3>
                <p className="text-sm text-muted leading-relaxed">{item.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Supported Languages */}
      <section id="languages" className="py-12 px-4 sm:px-6 lg:px-8 bg-mint/60 border-t border-[#176B35]/10">
        <div className="max-w-5xl mx-auto text-center space-y-6">
          <h2 className="text-2xl font-bold text-deep">Built for Multilingual Indian Farming</h2>
          <p className="text-sm text-muted max-w-xl mx-auto">
            Voice and advisory responses respect your selected language without unexpected switching.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            {SUPPORTED_LANGUAGES.map((lang) => (
              <div
                key={lang.code}
                className="inline-flex items-center gap-2 rounded-2xl bg-white px-4 py-2.5 border border-[#176B35]/15 shadow-sm"
              >
                <CheckCircle2 className="h-4 w-4 text-leaf" />
                <span className="text-sm font-bold text-deep">{lang.nativeName}</span>
                <span className="text-xs text-muted">({lang.name})</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-deep text-white/90 py-8 px-4 sm:px-6 lg:px-8 mt-auto">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-white px-2.5 py-1.5">
              <BrandLogo size="sm" />
            </div>
            <div>
              <p className="font-bold text-sm text-white">Raitha Mitra — Your Smart Farming Companion</p>
              <p className="text-white/70 mt-1">
                Data sources and external integrations are explicitly attributed and never fabricated.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/auth" className="hover:text-white underline">
              Farmer Sign In
            </Link>
            <Link to="/auth?mode=register" className="hover:text-white underline">
              Create Account
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
};
