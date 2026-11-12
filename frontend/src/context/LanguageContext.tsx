import React, { createContext, useContext, useState } from "react";
import type { LanguageCode } from "@/types";

export interface SupportedLanguage {
  code: LanguageCode;
  name: string;
  nativeName: string;
}

export const SUPPORTED_LANGUAGES: SupportedLanguage[] = [
  { code: "kn-IN", name: "Kannada", nativeName: "ಕನ್ನಡ" },
  { code: "hi-IN", name: "Hindi", nativeName: "हिन्दी" },
  { code: "te-IN", name: "Telugu", nativeName: "తెలుగు" },
  { code: "en-IN", name: "English", nativeName: "English" },
  { code: "ta-IN", name: "Tamil", nativeName: "தமிழ்" },
  { code: "mr-IN", name: "Marathi", nativeName: "मराठी" },
];

const UI_TRANSLATIONS: Record<LanguageCode, Record<string, string>> = {
  "kn-IN": {
    tagline: "ನಿಮ್ಮ ಸ್ಮಾರ್ಟ್ ಕೃಷಿ ಸಂಗಾತಿ",
    dashboard: "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
    voice: "ರೈತ ಮಿತ್ರ ಧ್ವನಿ",
    weather: "ಹವಾಮಾನ ಮತ್ತು ಪ್ರವಾಹ",
    soil: "ಮಣ್ಣಿನ ಆರೋಗ್ಯ",
    crops: "ಬೆಳೆ ಸಲಹೆ",
    growth: "ಬೆಳೆ ಬೆಳವಣಿಗೆ",
    pests: "ಕೀಟ ಮತ್ತು ರೋಗ",
    fertilizer: "ಗೊಬ್ಬರ ಯೋಜನೆ",
    yield: "ಇಳುವರಿ ಮತ್ತು ಕೊಯ್ಲು",
    nutrition: "ಪೋಷಣೆ ಮತ್ತು ಬಳಕೆ",
    mandi: "ಮಂಡಿ ಬೆಲೆಗಳು",
    profit: "ಲಾಭದ ಲೆಕ್ಕ",
    schemes: "ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು",
    profile: "ಪ್ರೊಫೈಲ್",
  },
  "hi-IN": {
    tagline: "आपका स्मार्ट खेती साथी",
    dashboard: "डैशबोर्ड",
    voice: "रैता मित्र आवाज़",
    weather: "मौसम और बाढ़",
    soil: "मिट्टी का स्वास्थ्य",
    crops: "फसल सलाह",
    growth: "फसल निगरानी",
    pests: "कीट और रोग",
    fertilizer: "उर्वरक योजना",
    yield: "उपज और कटाई",
    nutrition: "पोषण और उपयोग",
    mandi: "मंडी भाव",
    profit: "लाभ कैलकुलेटर",
    schemes: "सरकारी योजनाएं",
    profile: "प्रोफ़ाइल",
  },
  "te-IN": {
    tagline: "మీ స్మార్ట్ వ్యవసాయ సహచరుడు",
    dashboard: "డ్యాష్‌బోర్డ్",
    voice: "రైత మిత్ర వాయిస్",
    weather: "వాతావరణం & వరద",
    soil: "నేల ఆరోగ్యం",
    crops: "పంట సిఫార్సు",
    growth: "పంట పెరుగుదల",
    pests: "పురుగు & తెగులు",
    fertilizer: "ఎరువుల ప్రణాళిక",
    yield: "దిగుబడి & కోత",
    nutrition: "పోషణ & వినియోగం",
    mandi: "మండి ధరలు",
    profit: "లాభం లెక్కింపు",
    schemes: "ప్రభుత్వ పథకాలు",
    profile: "ప్రొఫైల్",
  },
  "en-IN": {
    tagline: "Your Smart Farming Companion",
    dashboard: "Dashboard",
    voice: "Voice Assistant",
    weather: "Weather & Flood",
    soil: "Soil Health",
    crops: "Crop Advice",
    growth: "Crop Growth",
    pests: "Pest & Disease",
    fertilizer: "Fertilizer",
    yield: "Yield & Harvest",
    nutrition: "Nutrition",
    mandi: "Mandi Prices",
    profit: "Profit Calculator",
    schemes: "Govt Schemes",
    profile: "Profile",
  },
  "ta-IN": {
    tagline: "உங்கள் ஸ்மார்ட் விவசாய துணை",
    dashboard: "முகப்பு",
    voice: "குரல் உதவியாளர்",
    weather: "வானிலை & வெள்ளம்",
    soil: "மண் வளம்",
    crops: "பயிர் பரிந்துரை",
    growth: "பயிர் வளர்ச்சி",
    pests: "பூச்சி & நோய்",
    fertilizer: "உர திட்டம்",
    yield: "மகசூல் & அறுவடை",
    nutrition: "ஊட்டச்சத்து",
    mandi: "சந்தை விலை",
    profit: "லாபக் கணக்கு",
    schemes: "அரசு திட்டங்கள்",
    profile: "சுயவிவரம்",
  },
  "mr-IN": {
    tagline: "तुमचा स्मार्ट शेती साथीदार",
    dashboard: "डॅशबोर्ड",
    voice: "व्हॉइस सहाय्यक",
    weather: "हवामान आणि पूर",
    soil: "माती आरोग्य",
    crops: "पीक सल्ला",
    growth: "पीक वाढ",
    pests: "कीड व रोग",
    fertilizer: "खत नियोजन",
    yield: "उत्पादन व कापणी",
    nutrition: "पोषण व वापर",
    mandi: "बाजारभाव",
    profit: "नफा कॅल्क्युलेटर",
    schemes: "शासकीय योजना",
    profile: "प्रोफाइल",
  },
};

interface LanguageContextValue {
  language: LanguageCode;
  setLanguage: (code: LanguageCode) => void;
  t: (key: string, fallback?: string) => string;
}

const LanguageContext = createContext<LanguageContextValue | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<LanguageCode>(() => {
    const saved = localStorage.getItem("raitha_mitra_lang") as LanguageCode | null;
    return saved || "en-IN";
  });

  const setLanguage = (code: LanguageCode) => {
    setLanguageState(code);
    localStorage.setItem("raitha_mitra_lang", code);
  };

  const t = (key: string, fallback?: string): string => {
    return UI_TRANSLATIONS[language]?.[key] || UI_TRANSLATIONS["en-IN"]?.[key] || fallback || key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export function useLanguage(): LanguageContextValue {
  const ctx = useContext(LanguageContext);
  if (!ctx) {
    throw new Error("useLanguage must be used inside LanguageProvider");
  }
  return ctx;
}
