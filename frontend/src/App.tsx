import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { LanguageProvider } from "@/context/LanguageContext";
import { AppLayout } from "@/components/layout/AppLayout";
import { LandingPage } from "@/pages/LandingPage";
import { AuthPage } from "@/pages/AuthPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { VoiceAssistantPage } from "@/pages/VoiceAssistantPage";
import { WeatherPage } from "@/pages/WeatherPage";
import { SoilHealthPage } from "@/pages/SoilHealthPage";
import { CropRecommendationPage } from "@/pages/CropRecommendationPage";
import { CropMonitoringPage } from "@/pages/CropMonitoringPage";
import { PestDetectionPage } from "@/pages/PestDetectionPage";
import { FertilizerPage } from "@/pages/FertilizerPage";
import { YieldPredictionPage } from "@/pages/YieldPredictionPage";
import { NutritionPage } from "@/pages/NutritionPage";
import { MandiPage } from "@/pages/MandiPage";
import { ProfitCalculatorPage } from "@/pages/ProfitCalculatorPage";
import { SchemesPage } from "@/pages/SchemesPage";
import { ProfilePage } from "@/pages/ProfilePage";
import { HarvestProtectionPage } from "@/pages/HarvestProtectionPage";
import { NotificationsPage } from "@/pages/NotificationsPage";

const ProtectedShell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center text-sm font-semibold text-forest">
        Loading Raitha Mitra...
      </div>
    );
  }
  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }
  return <AppLayout>{children}</AppLayout>;
};

export const App: React.FC = () => {
  return (
    <LanguageProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/auth" element={<AuthPage />} />
            <Route path="/login" element={<Navigate to="/auth" replace />} />
            <Route path="/register" element={<Navigate to="/auth?mode=register" replace />} />

            <Route path="/dashboard" element={<ProtectedShell><DashboardPage /></ProtectedShell>} />
            <Route path="/voice" element={<ProtectedShell><VoiceAssistantPage /></ProtectedShell>} />
            <Route path="/weather" element={<ProtectedShell><WeatherPage /></ProtectedShell>} />
            <Route path="/soil" element={<ProtectedShell><SoilHealthPage /></ProtectedShell>} />
            <Route path="/crops" element={<ProtectedShell><CropRecommendationPage /></ProtectedShell>} />
            <Route path="/growth" element={<ProtectedShell><CropMonitoringPage /></ProtectedShell>} />
            <Route path="/pest-detection" element={<ProtectedShell><PestDetectionPage /></ProtectedShell>} />
            <Route path="/fertilizer" element={<ProtectedShell><FertilizerPage /></ProtectedShell>} />
            <Route path="/yield" element={<ProtectedShell><YieldPredictionPage /></ProtectedShell>} />
            <Route path="/nutrition" element={<ProtectedShell><NutritionPage /></ProtectedShell>} />
            <Route path="/mandi" element={<ProtectedShell><MandiPage /></ProtectedShell>} />
            <Route path="/profit" element={<ProtectedShell><ProfitCalculatorPage /></ProtectedShell>} />
            <Route path="/schemes" element={<ProtectedShell><SchemesPage /></ProtectedShell>} />
            <Route path="/harvest" element={<ProtectedShell><HarvestProtectionPage /></ProtectedShell>} />
            <Route path="/notifications" element={<ProtectedShell><NotificationsPage /></ProtectedShell>} />
            <Route path="/profile" element={<ProtectedShell><ProfilePage /></ProtectedShell>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </LanguageProvider>
  );
};

export default App;
