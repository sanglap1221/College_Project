"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { LoadingSpinner } from "../../components/LoadingSpinner";
import { ReportForm } from "../../components/ReportForm";
import { useAuth } from "../../components/AuthProvider";
import AboutModal from "../../components/AboutModal";
import {
  generatePredictions,
  calculateReport,
  renderPdf,
  savePredictionSection,
  getAiConfig,
  updateAiConfig,
  API,
} from "../../services/api";
import type { ReportInput, ReportState } from "../../types/report";
import type {
  PredictionReport,
  PredictionSection,
  AiConfigResponse,
} from "../../types/predictions";

const initialFormValue: ReportInput = {
  name: "",
  father_name: "",
  dob: "2004-08-13",
  time: "14:42",
  place: "Kolkata",
  mobile: "",
  language: "bn",
  planet_overrides: {},
  override_moon_longitude: "",
  override_ascendant_longitude: "",
};

// Multilingual UI Dictionary for Complete Multilingual Experience (Section 21)
const UI_TEXT = {
  en: {
    chartSheet: "Chart Sheet",
    aiSettings: "AI Settings",
    about: "About",
    admin: "Admin",
    logout: "Logout",
    kundliTitle: "জীবন জিজ্ঞাসা — Kundli Birth Chart",
    predictionsTitle: "Predictions Workspace",
    simpleMode: "Simple Explanation",
    advancedMode: "Advanced Mode",
    lifeAreas: "Life Areas",
    overview: "Overview",
    currentPeriod: "Current Period",
    advanced: "Advanced",
    editClient: "Edit Client",
    hideDetails: "Hide Details",
    regenerate: "Regenerate",
    whyThisPrediction: "Why this prediction? (6-Point Parashari Basis)",
    coreThemes: "Core Symbolic Themes",
    growthChallenges: "Mindful Growth Challenges",
    supportingFactors: "Supporting Astrological Factors",
    modifyingFactors: "Modifying / Growth Factors",
    domainOverview: "Domain Synthesis & Overview",
    clickToView: "Click to view full details",
    executiveOverview: "Executive Natal Overview",
    activePeriods: "Active Vimshottari Dasha Periods",
    allLifeDomains: "All Life Domain Cards (Click Any Heading to View Details)",
    point1: "1. Planetary Placement Meaning",
    point2: "2. Specific Houses & Grahas Involved",
    point3: "3. Life Themes Connected",
    point4: "4. Astrological Relevance to this Prediction",
    point5: "5. Modifying Factors (Aspects, Dignity, Retrograde)",
    point6: "6. Synthesis of Supporting vs Modifying Factors",
    mahadasha: "Major Period (Mahadasha)",
    antardasha: "Sub-Period (Antardasha)",
    pratyantardasha: "Show Sub-Periods (Pratyantardasha)",
    hidePratyantardasha: "Hide Sub-Periods",
    evidenceLevel: "Evidence Level",
    lean: "Lean",
    parashariSystem: "Natal Astrological Analysis • Whole Sign Vedic Parashari",
    activeView: "Active View",
    verifiedBasis: "Verified Basis Rule IDs",
  },
  bn: {
    chartSheet: "ছক পত্র",
    aiSettings: "AI সেটিংস",
    about: "পরিচিতি",
    admin: "অ্যাডমিন",
    logout: "লগআউট",
    kundliTitle: "জীবন জিজ্ঞাসা — জন্মকুণ্ডলী ছক",
    predictionsTitle: "জ্যোতিষ ফলাফল কক্ষ",
    simpleMode: "সহজ বিশ্লেষণ (সাধারণ)",
    advancedMode: "উচ্চতর জ্যোতিষ বিচার",
    lifeAreas: "জীবনের বিভিন্ন ক্ষেত্র",
    overview: "সারসংক্ষেপ",
    currentPeriod: "বর্তমান দশা কাল",
    advanced: "উচ্চতর বিচার",
    editClient: "জন্ম বিবরণী সম্পাদন",
    hideDetails: "বিবরণী লুকান",
    regenerate: "পুনরায় গণনা",
    whyThisPrediction: "এই পূর্বাভাসের কারণ কী? (৬ দফা পরাশরী ভিত্তি)",
    coreThemes: "মূল চারিত্রিক ও গ্রহীয় সূত্র",
    growthChallenges: "সতর্কতা ও আত্মউন্নয়নের ক্ষেত্র",
    supportingFactors: "অনুকূল গ্রহীয় প্রভাব ও ভাবাধিপতি",
    modifyingFactors: "সংশোধনকারী ও আত্মউন্নয়ন প্রভাব",
    domainOverview: "ক্ষেত্রের সার্বিক তাৎপর্য",
    clickToView: "সম্পূর্ণ বিবরণ দেখতে ক্লিক করুন",
    executiveOverview: "সার্বিক কুণ্ডলী মূল্যায়ন",
    activePeriods: "সক্রিয় বিংশোত্তরী দশা চক্র",
    allLifeDomains: "জীবনের বিভিন্ন ক্ষেত্রের তালিকা (যেকোনো শিরোনামে ক্লিক করুন)",
    point1: "১. গ্রহাবস্থানের মূল তাৎপর্য",
    point2: "২. সংশ্লিষ্ট ভাব ও গ্রহসমূহ",
    point3: "৩. সংযুক্ত জীবনক্ষেত্র ও চারিত্রিক বৈশিষ্ট্য",
    point4: "৪. এই পূর্বাভাসের ক্ষেত্রে জ্যোতিষীয় প্রাসঙ্গিকতা",
    point5: "৫. সংশোধনকারী প্রভাব (দৃষ্টি, স্থানবল ও শুভাশুভ সম্বন্ধ)",
    point6: "৬. অনুকূল বনাম সতর্কতামূলক প্রভাবের সমন্বয়",
    mahadasha: "মহাদশা কাল",
    antardasha: "অন্তর্দশা কাল",
    pratyantardasha: "প্রত্যন্তর্দশা দেখুন",
    hidePratyantardasha: "প্রত্যন্তর্দশা লুকান",
    evidenceLevel: "প্রমাণ মাত্রা",
    lean: "ঝোঁক",
    parashariSystem: "বৈদিক পরাশরী জন্মকুণ্ডলী বিচার • সমগ্র রাশিচক্র",
    activeView: "সক্রিয় প্রদর্শন",
    verifiedBasis: "শাস্ত্রীয় সূত্রের পরিচিতি",
  },
  hi: {
    chartSheet: "कुंडली पत्र",
    aiSettings: "AI सेटिंग्स",
    about: "परिचय",
    admin: "व्यवस्थापक",
    logout: "लॉगआउट",
    kundliTitle: "जीवन जिज्ञासा — जन्मपत्रिका",
    predictionsTitle: "ज्योतिषीय भविष्यवाणी कक्ष",
    simpleMode: "सरल व्याख्या (सुबोध)",
    advancedMode: "विस्तृत ज्योतिष विश्लेषण",
    lifeAreas: "जीवन के विविध आयाम",
    overview: "संक्षिप्त परिचय",
    currentPeriod: "वर्तमान दशा काल",
    advanced: "उन्नत विश्लेषण",
    editClient: "जन्म विवरण बदलें",
    hideDetails: "विवरण छिपाएं",
    regenerate: "पुनः गणना",
    whyThisPrediction: "इस फलादेश का आधार क्या है? (६ सूत्रीय पराशरी प्रमाण)",
    coreThemes: "मुख्य सांकेतिक सूत्र",
    growthChallenges: "सावधानी एवं आत्मविकास के क्षेत्र",
    supportingFactors: "अनुकूल ग्रह स्थितियां एवं भावेश",
    modifyingFactors: "परिमार्जक एवं आत्मविकास प्रभाव",
    domainOverview: "क्षेत्र का समग्र फलादेश",
    clickToView: "पूर्ण विवरण देखने हेतु क्लिक करें",
    executiveOverview: "समग्र पत्रिका मूल्यांकन",
    activePeriods: "सक्रिय विंशोत्तरी दशा चक्र",
    allLifeDomains: "जीवन के समस्त आयाम (विवरण देखने हेतु क्लिक करें)",
    point1: "१. ग्रह स्थिति का मूल अभिप्राय",
    point2: "२. संबद्ध भाव एवं सक्रिय ग्रह",
    point3: "३. जुड़े हुए जीवन क्षेत्र एवं स्वभाव",
    point4: "४. इस फलादेश हेतु ज्योतिषीय प्रासंगिकता",
    point5: "५. परिमार्जक घटक (दृष्टि, बल एवं युति प्रभाव)",
    point6: "६. सकारात्मक बनाम परिमार्जक प्रभावों का समन्वय",
    mahadasha: "महादशा काल",
    antardasha: "अंतर्दशा काल",
    pratyantardasha: "प्रत्यंतर्दशा देखें",
    hidePratyantardasha: "प्रत्यंतर्दशा छिपाएं",
    evidenceLevel: "प्रमाण स्तर",
    lean: "प्रवृत्ति",
    parashariSystem: "वैदिक पराशरी जन्मपत्रिका फलादेश • संपूर्ण राशि चक्र",
    activeView: "सक्रिय दृश्य",
    verifiedBasis: "प्रमाणित शास्त्रीय सूत्र",
  },
};

// Evidence Level and Lean Translation Dictionaries
const EVIDENCE_LEVEL_MAP: Record<string, Record<string, string>> = {
  bn: {
    "Convergent": "সুসংহত",
    "Moderate": "মধ্যম",
    "Strong": "দৃঢ়",
    "Divergent": "বৈচিত্র্যপূর্ণ",
    "Emerging": "উদ্ীয়মান"
  },
  hi: {
    "Convergent": "सुसंबद्ध",
    "Moderate": "मध्यम",
    "Strong": "प्रबल",
    "Divergent": "विविध",
    "Emerging": "उदीयमान"
  },
  en: {
    "Convergent": "Convergent",
    "Moderate": "Moderate",
    "Strong": "Strong",
    "Divergent": "Divergent",
    "Emerging": "Emerging"
  }
};

const LEAN_MAP: Record<string, Record<string, string>> = {
  bn: {
    "supportive": "অনুকূল",
    "challenging": "চ্যালেঞ্জিং",
    "mixed": "মিশ্র",
    "favorable": "অনুকূল",
    "cautious": "সতর্কতামূলক"
  },
  hi: {
    "supportive": "अनुकूल",
    "challenging": "चुनौतीपूर्ण",
    "mixed": "मिश्रित",
    "favorable": "अनुकूल",
    "cautious": "सतर्क"
  },
  en: {
    "supportive": "Supportive",
    "challenging": "Challenging",
    "mixed": "Mixed",
    "favorable": "Favorable",
    "cautious": "Cautious"
  }
};

// Client-Side Rule Explainer and Sanitizer to ensure NO raw rule IDs leak in Simple Mode
function cleanRuleText(text: string): string {
  if (!text) return "";
  return text
    .replace(/\[\s*(HL|PH|DG|YOGA)[\w\-]+\s*\]/gi, "")
    .replace(/\b(HL|PH|DG|YOGA)[\w\-]+\b/gi, "")
    .replace(/\[\s*\]/g, "")
    .replace(/\(\s*\)/g, "")
    .replace(/\s+/g, " ")
    .replace(/\s+\./g, ".")
    .replace(/\.\s*\./g, ".")
    .trim();
}

function explainRuleClient(ruleId: string, lang: "en" | "bn" | "hi"): string {
  const cleanId = String(ruleId || "").trim();
  const hlMatch = cleanId.match(/^HL-H(\d+)-IN-H(\d+)$/i);
  if (hlMatch) {
    const h1 = parseInt(hlMatch[1], 10);
    const h2 = parseInt(hlMatch[2], 10);
    if (lang === "bn") {
      return `আপনার ${h1}ম ভাবাধিপতি ${h2}ম ভাবে অবস্থান করছে। প্রচলিত বৈদিক জ্যোতিষ মতে, এটি উভয় ভাবের মধ্যে পারস্পরিক শক্তি ও শুভ সংযোগ নির্দেশ করে।`;
    } else if (lang === "hi") {
      return `आपके ${h1}वें भाव का स्वामी ${h2}वें भाव में स्थित है, जो दोनों भावों के मध्य सकारात्मक तालमेल स्थापित करता है।`;
    } else {
      return `The ruler of your ${h1}th house is placed in your ${h2}th house, connecting their core themes in your natal chart.`;
    }
  }

  const phMatch = cleanId.match(/^PH-([A-Z]+)-H(\d+)$/i);
  if (phMatch) {
    const p = phMatch[1];
    const h = parseInt(phMatch[2], 10);
    if (lang === "bn") {
      return `${p} গ্রহ আপনার ${h}ম ভাবে অবস্থান করছে, যা জীবনের এই ক্ষেত্রে স্বাভাবিক কর্মক্ষমতা বৃদ্ধি করে।`;
    } else if (lang === "hi") {
      return `${p} ग्रह आपके ${h}वें भाव में स्थित है, जो इस क्षेत्र में स्वाभाविक ऊर्जा प्रदान करता है।`;
    } else {
      return `${p} is positioned in your ${h}th house, directing focused planetary vitality into this domain.`;
    }
  }

  if (cleanId.startsWith("YOGA-")) {
    if (lang === "bn") {
      return `আপনার জন্মকুণ্ডলীতে শাস্ত্রীয় শুভ গ্রহ সমাবেশ এই ক্ষেত্রে বিশেষ উন্নতি সাধনে সহায়ক।`;
    } else if (lang === "hi") {
      return `आपकी जन्मपत्रिका में शास्त्रीय ग्रह योग इस क्षेत्र में उल्लेखनीय सफलता का संकेत देता है।`;
    } else {
      return `A classical planetary yoga creates an auspicious alignment for steady accomplishment here.`;
    }
  }

  return "";
}

export default function PredictionsPage() {
  const router = useRouter();
  const { user, isAdmin, logout } = useAuth();

  // Core Form & Prediction States
  const [formValue, setFormValue] = useState<ReportInput>(initialFormValue);
  const [showBirthForm, setShowBirthForm] = useState(false);
  const [predictionReport, setPredictionReport] = useState<PredictionReport | null>(null);

  // Section 20 & 21 States: Explanation Mode & Multilingual Language
  const [explanationMode, setExplanationMode] = useState<"simple" | "advanced">("simple");
  const [selectedLang, setSelectedLang] = useState<"en" | "bn" | "hi">("bn");

  // Left Column: "জীবন জিজ্ঞাসা" Kundli Chart PDF & Preview States
  const [chartPdfUrl, setChartPdfUrl] = useState<string>("");
  const [chartDownloadUrl, setChartDownloadUrl] = useState<string>("");
  const [chartLanguage, setChartLanguage] = useState<string>("bn");
  const [chartLoading, setChartLoading] = useState<boolean>(false);
  const [chartZoom, setChartZoom] = useState<number>(0.8);
  const chartIframeRef = useRef<HTMLIFrameElement | null>(null);
  const leftColContainerRef = useRef<HTMLDivElement | null>(null);

  // Right Column: Predictions Navigation & Details
  const [activeTab, setActiveTab] = useState<"life_areas" | "overview" | "current_period" | "advanced">("life_areas");
  const [selectedTopic, setSelectedTopic] = useState<string>("finance");
  const [expandedWhyThis, setExpandedWhyThis] = useState<Record<string, boolean>>({});
  const [showPratyantardasha, setShowPratyantardasha] = useState<boolean>(false);

  // Manual Editing Drawer (inside Advanced)
  const [isEditDrawerOpen, setIsEditDrawerOpen] = useState(false);
  const [editingTopic, setEditingTopic] = useState<string>("finance");
  const [editContent, setEditContent] = useState<string>("");
  const [savingSection, setSavingSection] = useState(false);

  // General Loading & Feedback States
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [successMessage, setSuccessMessage] = useState<string>("");

  // AI Configuration States
  const [useAi, setUseAi] = useState<boolean>(true);
  const [aiConfig, setAiConfig] = useState<AiConfigResponse | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<string>("groq");
  const [selectedModel, setSelectedModel] = useState<string>("llama-3.3-70b-versatile");
  const [aiSettingsOpen, setAiSettingsOpen] = useState(false);
  const [apiKeyInput, setApiKeyInput] = useState("");

  const [isAboutOpen, setIsAboutOpen] = useState(false);
  const detailsContainerRef = useRef<HTMLDivElement | null>(null);

  // Active UI dictionary
  const ui = UI_TEXT[selectedLang] || UI_TEXT["en"];

  // ── Auto-Fit Kundli Sheet Zoom on Resize ──
  useEffect(() => {
    function computeZoom() {
      if (leftColContainerRef.current) {
        const availableW = leftColContainerRef.current.clientWidth - 28;
        if (availableW > 200) {
          const fit = Math.min(1.0, Math.max(0.55, availableW / 794));
          setChartZoom(Number(fit.toFixed(2)));
        }
      }
    }
    computeZoom();
    window.addEventListener("resize", computeZoom);
    return () => window.removeEventListener("resize", computeZoom);
  }, []);

  // ── 1. Load Kundli Chart Sheet ("জীবন জিজ্ঞাসা") ──
  const loadChartReport = useCallback(
    async (input: ReportInput, lang: string = "bn") => {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);
      try {
        setChartLoading(true);
        const calc = await calculateReport({ ...input, language: lang }, controller.signal);
        const pdfRes = await renderPdf(calc, controller.signal);
        setChartPdfUrl(pdfRes.preview_url);
        setChartDownloadUrl(pdfRes.compiled_pdf_url);
      } catch (err: any) {
        if (err.name === "AbortError") {
          console.warn("Kundli Chart preview generation timed out after 30 seconds.");
          setError("Kundli Chart preview generation timed out after 30 seconds.");
        } else {
          console.warn("Could not compile Kundli Chart preview:", err);
        }
      } finally {
        clearTimeout(timeoutId);
        setChartLoading(false);
      }
    },
    []
  );

  // ── 2. Generate Natal Predictions ──
  const handleGeneratePredictions = useCallback(
    async (input: ReportInput, force: boolean = false, langOverride?: string) => {
      if (!input.name || !input.dob || !input.time || !input.place) {
        setShowBirthForm(true);
        return;
      }

      setLoading(true);
      setError("");
      setSuccessMessage("");

      const activeLang = langOverride || selectedLang || input.language || "bn";

      try {
        const reportId = predictionReport?.report_id || `pred-${Date.now().toString(36)}`;
        const report = await generatePredictions({
          report_id: reportId,
          customer_data: input,
          use_ai: useAi,
          provider: selectedProvider,
          model: selectedModel,
          force_regenerate: force,
          language: activeLang,
        });

        setPredictionReport(report);
        setShowBirthForm(false);
        setSuccessMessage(
          activeLang === "bn"
            ? "পরাশরী জ্যোতিষ সূত্রানুযায়ী সম্পূর্ণ পূর্বাভাস প্রস্তুত হয়েছে!"
            : activeLang === "hi"
            ? "पराशरी ज्योतिष सूत्रों के आधार पर फलादेश सफलतापूर्वक तैयार किया गया!"
            : "Predictions generated successfully with Jyotish Rulebook v2.0!"
        );
        setTimeout(() => setSuccessMessage(""), 4000);
      } catch (err: any) {
        console.error("Prediction generation error:", err);
        setError(err.message || "Failed to generate predictions.");
      } finally {
        setLoading(false);
      }
    },
    [predictionReport?.report_id, selectedLang, selectedModel, selectedProvider, useAi]
  );

  // ── 3. Initial Load from Session Storage or History ──
  useEffect(() => {
    if (typeof window !== "undefined") {
      getAiConfig()
        .then((cfg) => {
          if (cfg) {
            setAiConfig(cfg);
            if (cfg.active_provider && cfg.active_provider !== "none") {
              setSelectedProvider(cfg.active_provider);
              setSelectedModel(cfg.active_model);
            }
          }
        })
        .catch((err) => console.warn("Could not load AI config:", err));

      const passedPred = sessionStorage.getItem("pending_prediction_details");
      const passedBirth = sessionStorage.getItem("pending_birth_details");
      const activeData = passedPred || passedBirth;

      if (activeData) {
        try {
          const parsed = JSON.parse(activeData) as ReportInput;
          setFormValue(parsed);
          const lang = (parsed.language || "bn") as "en" | "bn" | "hi";
          setSelectedLang(lang);
          setChartLanguage(lang);

          // Load Chart and Predictions truly in parallel
          Promise.allSettled([
            loadChartReport(parsed, lang),
            handleGeneratePredictions(parsed, false, lang),
          ]);
        } catch (e) {
          console.error("Error reading stored prediction details:", e);
        }
      } else {
        setShowBirthForm(true);
      }
    }
  }, [handleGeneratePredictions, loadChartReport]);

  // ── 4. Global Language Selector Handler ──
  const handleLanguageChange = (newLang: "en" | "bn" | "hi") => {
    setSelectedLang(newLang);
    setChartLanguage(newLang);
    const updated = { ...formValue, language: newLang };
    setFormValue(updated);

    if (typeof window !== "undefined") {
      sessionStorage.setItem("pending_prediction_details", JSON.stringify(updated));
    }

    loadChartReport(updated, newLang);
    handleGeneratePredictions(updated, true, newLang);
  };

  // ── 5. Select Topic Handler ──
  const handleSelectTopic = (topicKey: string) => {
    setSelectedTopic(topicKey);
    setActiveTab("life_areas");
    if (detailsContainerRef.current) {
      detailsContainerRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  // ── 6. Print Kundli Chart ──
  const handlePrintChart = () => {
    if (chartIframeRef.current && chartIframeRef.current.contentWindow) {
      chartIframeRef.current.contentWindow.focus();
      chartIframeRef.current.contentWindow.print();
    } else if (chartPdfUrl) {
      window.open(chartPdfUrl, "_blank");
    }
  };

  // ── 7. Save Manual Section Edit ──
  async function handleSaveSectionEdit() {
    if (!predictionReport) return;
    setSavingSection(true);
    try {
      await savePredictionSection(predictionReport.report_id, editingTopic, editContent);
      setPredictionReport((prev) => {
        if (!prev) return prev;
        const nextSections = prev.sections.map((s) =>
          s.topic === editingTopic ? { ...s, prediction: editContent, overview: editContent, status: "manual_edited" } : s
        );
        return { ...prev, sections: nextSections };
      });
      setIsEditDrawerOpen(false);
      setSuccessMessage(`Section '${editingTopic}' updated successfully!`);
      setTimeout(() => setSuccessMessage(""), 4000);
    } catch (err: any) {
      setError(err.message || "Failed to save section edits.");
    } finally {
      setSavingSection(false);
    }
  }

  // ── 8. Save AI Settings ──
  async function handleSaveAiSettings() {
    try {
      await updateAiConfig({
        provider: selectedProvider,
        model: selectedModel,
        api_key: apiKeyInput || undefined,
      });
      const updated = await getAiConfig();
      if (updated) setAiConfig(updated);
      setAiSettingsOpen(false);
      setSuccessMessage("AI engine settings updated.");
      setTimeout(() => setSuccessMessage(""), 4000);
    } catch (err: any) {
      setError(err.message || "Failed to update AI settings.");
    }
  }

  // Active section resolution
  const activeSection = useMemo(() => {
    if (!predictionReport || !predictionReport.sections || predictionReport.sections.length === 0) return null;
    const key = selectedTopic.toLowerCase();
    const found = predictionReport.sections.find(
      (s) => s.topic.toLowerCase() === key || s.title.toLowerCase().includes(key)
    );
    return found || predictionReport.sections[0] || null;
  }, [predictionReport, selectedTopic]);

  // Multilingual active section data
  const localizedActiveSection = useMemo(() => {
    if (!activeSection) return null;
    const tr = activeSection.translations?.[selectedLang];
    let overviewText = tr?.overview || activeSection.overview || activeSection.summary || "";

    if (explanationMode === "simple") {
      overviewText = cleanRuleText(overviewText);
      if (selectedLang === "bn") {
        overviewText = overviewText
          .replace(/\bmixed\b/gi, "মিশ্র")
          .replace(/\bmoderate\b/gi, "মধ্যম")
          .replace(/\bsupportive\b/gi, "অনুকূল")
          .replace(/mixed-/g, "মিশ্র প্রকৃতির ")
          .replace(/mixed/g, "মিশ্র");
      } else if (selectedLang === "hi") {
        overviewText = overviewText
          .replace(/\bmixed\b/gi, "मिश्रित")
          .replace(/\bmoderate\b/gi, "मध्यम")
          .replace(/\bsupportive\b/gi, "अनुकूल")
          .replace(/mixed-/g, "मिश्रित प्रकृति का ")
          .replace(/mixed/g, "मिश्रित");
      }
    }

    return {
      topic: activeSection.topic,
      career_analysis: activeSection.career_analysis,
      title: tr?.title || activeSection.title,
      overview: overviewText,
      themes: tr?.themes && tr.themes.length > 0 ? tr.themes : activeSection.themes || [],
      challenges: tr?.challenges && tr.challenges.length > 0 ? tr.challenges : activeSection.challenges || [],
      why_this: activeSection.why_this,
      supporting_factors: activeSection.supporting_factors || [],
      challenging_factors: activeSection.challenging_factors || [],
      evidence_level: activeSection.evidence_level,
      lean: activeSection.lean,
      basis_ids: activeSection.basis_ids || activeSection.rule_ids || [],
      explanation: activeSection.explanation,
    };
  }, [activeSection, selectedLang, explanationMode]);

  // Multilingual executive overview
  const localizedExecutiveOverview = useMemo(() => {
    if (!predictionReport) return "";
    const tr = (predictionReport as any).translations?.executive_overview;
    if (tr && tr[selectedLang]) return tr[selectedLang];
    return (
      predictionReport.executive_overview ||
      "Your natal chart reveals purposeful planetary vigor across foundational houses. Parashari principles indicate steady progressive cultivation when natural talents are paired with structured discipline."
    );
  }, [predictionReport, selectedLang]);

  const toggleWhyThis = (key: string) => {
    setExpandedWhyThis((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const currentDasha = useMemo(() => {
    if (!predictionReport?.dasha_summary) return null;
    const md = predictionReport.dasha_summary.find((d) => d.level === "mahadasha");
    const ad = predictionReport.dasha_summary.find((d) => d.level === "antardasha");
    return { md, ad };
  }, [predictionReport]);

  return (
    <div className="h-screen w-full flex flex-col font-sans bg-[#f7f5f0] text-slate-800 overflow-hidden">
      {/* ── Top Header Navigation Bar (Styled cleanly matching first page) ── */}
      <header className="h-[60px] shrink-0 bg-[#fdfcf7] border-b border-[#ebdcb9] z-30 shadow-xs flex items-center px-3 sm:px-5">
        <div className="w-full flex items-center justify-between">
          <div className="flex items-center gap-2.5 sm:gap-3">
            <button
              onClick={() => router.push("/create-report")}
              className="w-8 h-8 rounded-lg bg-[#fffbeb] hover:bg-amber-100 flex items-center justify-center text-[#92400e] border border-amber-200 shadow-xs transition-colors"
              title="Return to Visual Editor Sheet"
            >
              <i className="fa-solid fa-arrow-left text-xs"></i>
            </button>
            <div className="flex items-center gap-2">
              <span className="w-8 h-8 rounded-lg bg-[#800020] text-amber-300 flex items-center justify-center font-bold text-base shadow-xs">
                🕉️
              </span>
              <div>
                <h1 className="font-serif font-bold text-sm sm:text-base text-[#800020] leading-none">
                  জীবন জিজ্ঞাসা — Predictions Workspace
                </h1>
                <p className="text-[10px] text-amber-900 font-medium tracking-wide">
                  Complete Jyotish Natal Analysis &amp; AI Consistency Audit
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Global Language Selector (English | বাংলা | हिन्दी) */}
            <div className="flex items-center bg-white p-0.5 rounded-lg border border-amber-200 shadow-2xs">
              <button
                onClick={() => handleLanguageChange("bn")}
                className={`px-2 py-0.5 text-xs font-bold rounded transition-colors ${
                  selectedLang === "bn" ? "bg-[#800020] text-white shadow-2xs" : "text-amber-900 hover:bg-amber-50"
                }`}
                title="বাংলা ভাষায় দেখুন"
              >
                বাংলা
              </button>
              <button
                onClick={() => handleLanguageChange("en")}
                className={`px-2 py-0.5 text-xs font-bold rounded transition-colors ${
                  selectedLang === "en" ? "bg-[#800020] text-white shadow-2xs" : "text-amber-900 hover:bg-amber-50"
                }`}
                title="View in English"
              >
                English
              </button>
              <button
                onClick={() => handleLanguageChange("hi")}
                className={`px-2 py-0.5 text-xs font-bold rounded transition-colors ${
                  selectedLang === "hi" ? "bg-[#800020] text-white shadow-2xs" : "text-amber-900 hover:bg-amber-50"
                }`}
                title="हिन्दी में देखें"
              >
                हिन्दी
              </button>
            </div>

            <button
              onClick={() => router.push("/")}
              className="px-2.5 py-1.5 rounded-lg border border-[#ebdcb9] hover:bg-amber-50 text-amber-900 text-xs font-semibold hidden sm:flex items-center gap-1.5 transition-colors shadow-2xs"
            >
              <i className="fa-solid fa-chart-pie text-xs"></i> {ui.chartSheet}
            </button>

            <button
              onClick={() => setAiSettingsOpen(true)}
              className="px-2.5 py-1.5 rounded-lg bg-indigo-50 border border-indigo-200 hover:bg-indigo-100 text-indigo-900 text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <i className="fa-solid fa-microchip text-xs"></i> {ui.aiSettings}
            </button>

            <button
              onClick={() => setIsAboutOpen(true)}
              className="px-2.5 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-medium hidden md:flex items-center gap-1"
            >
              <i className="fa-solid fa-circle-info text-xs"></i> {ui.about}
            </button>

            {isAdmin && (
              <Link
                href="/admin"
                className="px-2.5 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-medium flex items-center gap-1"
              >
                <i className="fa-solid fa-shield text-xs"></i> {ui.admin}
              </Link>
            )}

            <button
              onClick={logout}
              className="px-2.5 py-1.5 rounded-lg border border-red-200 text-red-700 hover:bg-red-50 text-xs font-medium flex items-center gap-1 transition-colors"
            >
              <i className="fa-solid fa-arrow-right-from-bracket text-xs"></i> {ui.logout}
            </button>
          </div>
        </div>
      </header>

      {/* ── Status Alerts ── */}
      {error && (
        <div className="shrink-0 w-full px-4 pt-2">
          <div className="bg-red-50 border border-red-200 rounded-lg p-2 text-red-800 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <i className="fa-solid fa-triangle-exclamation text-red-600"></i>
              <span>{error}</span>
            </div>
            <button onClick={() => setError("")} className="font-bold text-red-500 hover:text-red-800">
              ✕
            </button>
          </div>
        </div>
      )}

      {successMessage && (
        <div className="shrink-0 w-full px-4 pt-2">
          <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-2 text-emerald-800 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <i className="fa-solid fa-circle-check text-emerald-600"></i>
              <span>{successMessage}</span>
            </div>
            <button onClick={() => setSuccessMessage("")} className="font-bold text-emerald-500 hover:text-emerald-800">
              ✕
            </button>
          </div>
        </div>
      )}

      {/* ── Main Workspace: Full Width Responsive Grid matching First Page ── */}
      <main className="flex-1 w-full px-2 sm:px-4 py-2.5 grid grid-cols-12 gap-3 min-h-0 overflow-hidden">
        {/* ════════════ LEFT COLUMN: "জীবন জিজ্ঞাসা" KUNDLI CHART PDF PREVIEW (6 Cols) ════════════ */}
        <section className="col-span-12 lg:col-span-6 h-full flex flex-col min-h-0 overflow-hidden bg-white border border-[#ebdcb9] rounded-xl shadow-xs">
          {/* Header Bar matching first page */}
          <div className="shrink-0 px-3 py-2 bg-[#fdfcf7] border-b border-[#ebdcb9] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <i className="fa-solid fa-file-pdf text-[#800020] text-sm"></i>
              <span className="font-serif font-bold text-xs text-slate-800">
                {ui.kundliTitle}
              </span>
            </div>

            <div className="flex items-center gap-1.5 sm:gap-2">
              {/* Language Selector matching first page */}
              <div className="relative">
                <select
                  value={chartLanguage}
                  onChange={(e) => handleLanguageChange(e.target.value as any)}
                  className="rounded-lg pl-2.5 pr-6 py-1 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 appearance-none cursor-pointer outline-none shadow-2xs"
                >
                  <option value="bn">বাংলা (Bengali)</option>
                  <option value="en">English (English)</option>
                  <option value="hi">हिंदी (Hindi)</option>
                </select>
                <span className="absolute inset-y-0 right-2 flex items-center pointer-events-none text-slate-400 text-[9px]">
                  <i className="fa-solid fa-chevron-down"></i>
                </span>
              </div>

              {/* Responsive Zoom Controls */}
              <div className="flex items-center bg-slate-100 rounded-lg p-0.5 text-xs text-slate-700 border border-slate-200">
                <button
                  onClick={() => setChartZoom((z) => Math.max(0.55, Number((z - 0.08).toFixed(2))))}
                  className="w-5 h-5 flex items-center justify-center hover:bg-white rounded font-bold"
                  title="Zoom Out"
                >
                  -
                </button>
                <button
                  onClick={() => {
                    if (leftColContainerRef.current) {
                      const w = leftColContainerRef.current.clientWidth - 28;
                      setChartZoom(Number(Math.min(1.0, Math.max(0.55, w / 794)).toFixed(2)));
                    }
                  }}
                  className="px-1 text-[10px] font-mono font-semibold hover:bg-white rounded"
                  title="Fit Width"
                >
                  {Math.round(chartZoom * 100)}%
                </button>
                <button
                  onClick={() => setChartZoom((z) => Math.min(1.3, Number((z + 0.08).toFixed(2))))}
                  className="w-5 h-5 flex items-center justify-center hover:bg-white rounded font-bold"
                  title="Zoom In"
                >
                  +
                </button>
              </div>

              {/* Open in new tab */}
              {chartPdfUrl && (
                <a
                  href={chartDownloadUrl || chartPdfUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="px-2 py-1 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 rounded-lg flex items-center gap-1 shadow-2xs transition-colors"
                  title="Open Chart in New Tab"
                >
                  <i className="fa-solid fa-up-right-from-square text-[10px]"></i> Open
                </a>
              )}

              {/* Print Button */}
              <button
                onClick={handlePrintChart}
                className="px-2.5 py-1 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg flex items-center gap-1 shadow-2xs transition-colors"
                title="Print Kundli Chart"
              >
                <i className="fa-solid fa-print text-[10px]"></i> Print
              </button>

              {/* Download PDF Button */}
              {chartDownloadUrl && (
                <a
                  href={chartDownloadUrl}
                  download={`${formValue.name || "Kundli"}_Jiban_Jigyasa.pdf`}
                  className="px-2.5 py-1 text-xs font-semibold text-white bg-[#800020] hover:bg-[#600018] rounded-lg flex items-center gap-1 shadow-2xs transition-colors"
                  title="Download Kundli PDF"
                >
                  <i className="fa-solid fa-download text-[10px]"></i> PDF
                </a>
              )}
            </div>
          </div>

          {/* Kundli Chart Preview Frame with Responsive Auto-Fit (Zero Clipping) */}
          <div
            ref={leftColContainerRef}
            className="flex-1 min-h-0 bg-[#f1f5f9] relative overflow-y-auto overflow-x-hidden p-3 flex justify-center items-start"
          >
            {chartLoading && (
              <div className="absolute inset-0 bg-white/85 backdrop-blur-xs flex flex-col items-center justify-center gap-2 z-10 text-slate-600">
                <LoadingSpinner />
                <span className="text-xs font-medium">Rendering Kundli Birth Chart...</span>
              </div>
            )}

            {chartPdfUrl ? (
              <div
                style={{
                  width: "210mm",
                  maxWidth: "794px",
                  transform: `scale(${chartZoom})`,
                  transformOrigin: "top center",
                  marginBottom: chartZoom < 1 ? `${(1 - chartZoom) * -1120}px` : "16px",
                  transition: "transform 0.15s ease",
                }}
                className="flex justify-center"
              >
                <iframe
                  ref={chartIframeRef}
                  src={chartPdfUrl}
                  className="w-[210mm] h-[297mm] min-h-[1050px] border border-slate-300 rounded-lg shadow-md bg-white"
                  title="Kundli Birth Chart — জীবন জিজ্ঞাসা"
                />
              </div>
            ) : (
              <div className="p-8 text-center text-slate-400 flex flex-col items-center gap-2 my-auto">
                <div className="w-12 h-12 rounded-full bg-amber-50 text-amber-800 flex items-center justify-center text-xl">
                  📜
                </div>
                <h4 className="font-serif font-bold text-xs text-slate-600">No Chart Preview Available</h4>
                <p className="text-[11px] text-slate-400 max-w-xs">
                  Fill in birth details to generate the verified "জীবন জিজ্ঞাসা" Kundli Chart Sheet.
                </p>
                <button
                  onClick={() => loadChartReport(formValue, chartLanguage)}
                  className="mt-1 px-3 py-1 bg-[#800020] text-white rounded-lg text-xs font-semibold shadow-2xs"
                >
                  Generate Kundli
                </button>
              </div>
            )}
          </div>
        </section>

        {/* ════════════ RIGHT COLUMN: INTERACTIVE PREDICTIONS WORKSPACE (6 Cols) ════════════ */}
        <section className="col-span-12 lg:col-span-6 h-full flex flex-col min-h-0 overflow-hidden bg-white border border-[#ebdcb9] rounded-xl shadow-xs">
          {/* Top Prediction Controls Toolbar */}
          <div className="shrink-0 px-3 py-2 bg-[#fdfcf7] border-b border-[#ebdcb9] flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="font-serif font-bold text-xs text-[#800020] flex items-center gap-1.5">
                <i className="fa-solid fa-wand-magic-sparkles"></i> {ui.predictionsTitle}
              </span>

              {/* Mode Toggle: Simple Explanation vs Advanced Mode (Section 20.C) */}
              <div className="flex items-center bg-slate-100 p-0.5 rounded-lg border border-slate-200">
                <button
                  onClick={() => setExplanationMode("simple")}
                  className={`px-2 py-0.5 text-[11px] font-semibold rounded transition-colors ${
                    explanationMode === "simple"
                      ? "bg-white text-emerald-800 shadow-2xs border border-emerald-300"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                  title="Human-friendly explanation without raw rule IDs"
                >
                  <i className="fa-solid fa-user text-[10px] mr-1"></i>
                  {ui.simpleMode}
                </button>
                <button
                  onClick={() => setExplanationMode("advanced")}
                  className={`px-2 py-0.5 text-[11px] font-semibold rounded transition-colors ${
                    explanationMode === "advanced"
                      ? "bg-white text-indigo-900 shadow-2xs border border-indigo-300"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                  title="Astrological mode with rule IDs, dignity, and conditions"
                >
                  <i className="fa-solid fa-microscope text-[10px] mr-1"></i>
                  {ui.advancedMode}
                </button>
              </div>

              <button
                onClick={() => setShowBirthForm(!showBirthForm)}
                className="text-[11px] text-amber-800 hover:underline flex items-center gap-1 font-sans ml-1"
              >
                <i className="fa-solid fa-id-card"></i> {showBirthForm ? ui.hideDetails : ui.editClient}
              </button>
            </div>

            <div className="flex items-center gap-2">
              {/* AI Provider & Model Controls */}
              <select
                value={selectedProvider}
                onChange={(e) => setSelectedProvider(e.target.value)}
                className="text-xs py-1 px-1.5 border border-slate-200 rounded-md bg-slate-50 focus:bg-white text-slate-700"
              >
                <option value="groq">Groq (Ultra-Fast Free)</option>
                <option value="gemini">Google Gemini</option>
                <option value="openrouter">OpenRouter</option>
                <option value="custom">Custom Endpoint</option>
              </select>

              <button
                onClick={() => handleGeneratePredictions(formValue, true, selectedLang)}
                disabled={loading}
                className="px-3 py-1 rounded-lg bg-[#800020] hover:bg-[#600018] text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-2xs disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <LoadingSpinner /> Generating...
                  </>
                ) : (
                  <>
                    <i className="fa-solid fa-rotate text-xs"></i> {ui.regenerate}
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Client Details Form Drawer */}
          {showBirthForm && (
            <div className="shrink-0 p-3 bg-amber-50/40 border-b border-amber-200 max-h-48 overflow-y-auto">
              <ReportForm
                value={formValue}
                onChange={setFormValue}
                onSubmit={() => {
                  loadChartReport(formValue, chartLanguage);
                  handleGeneratePredictions(formValue, true, selectedLang);
                }}
                loading={loading}
              />
            </div>
          )}

          {/* View Mode Tabs (Life Areas | Overview | Current Period | Advanced) */}
          <div className="shrink-0 flex items-center justify-between border-b border-slate-200 bg-white px-3 pt-1.5">
            <div className="flex items-center gap-1">
              {[
                { id: "life_areas", label: ui.lifeAreas, icon: "fa-layer-group" },
                { id: "overview", label: ui.overview, icon: "fa-compass" },
                { id: "current_period", label: ui.currentPeriod, icon: "fa-clock" },
                { id: "advanced", label: ui.advanced, icon: "fa-code-branch" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`px-3 py-1.5 text-xs font-semibold border-b-2 flex items-center gap-1.5 transition-colors ${
                    activeTab === tab.id
                      ? "border-[#800020] text-[#800020] bg-amber-50/50"
                      : "border-transparent text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <i className={`fa-solid ${tab.icon} text-[11px]`}></i>
                  {tab.label}
                </button>
              ))}
            </div>

            {predictionReport && (
              <span className="text-[10px] font-mono text-amber-900 hidden sm:inline-block">
                Parashari v{predictionReport.ruleset.version}
              </span>
            )}
          </div>

          {/* Interactive Topic Heading Pills Strip (Clicking any heading immediately shows details) */}
          {predictionReport?.sections && (
            <div className="shrink-0 px-3 py-1.5 border-b border-slate-100 bg-[#faf9f5] flex items-center gap-1.5 overflow-x-auto no-scrollbar">
              {predictionReport.sections.map((sec) => {
                const isSelected =
                  sec.topic.toLowerCase() === selectedTopic.toLowerCase() ||
                  sec.title.toLowerCase().includes(selectedTopic.toLowerCase());
                const trTitle = sec.translations?.[selectedLang]?.title || sec.title;

                return (
                  <button
                    key={sec.topic}
                    onClick={() => handleSelectTopic(sec.topic)}
                    className={`px-2.5 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-all flex items-center gap-1.5 shrink-0 ${
                      isSelected
                        ? "bg-[#800020] text-white font-semibold shadow-xs ring-1 ring-[#800020]"
                        : "bg-white hover:bg-amber-50 text-slate-700 border border-slate-200"
                    }`}
                  >
                    <span>{trTitle}</span>
                    <span
                      className={`text-[9px] px-1 py-0.2 rounded font-bold uppercase ${
                        isSelected ? "bg-amber-200/40 text-amber-100" : "bg-slate-100 text-slate-500"
                      }`}
                    >
                      {sec.evidence_level}
                    </span>
                  </button>
                );
              })}
            </div>
          )}

          {/* Scrollable Prediction Details Content Area */}
          <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-4">
            {/* ── TAB: LIFE AREAS (CLICK HEADING OR CARD TO VIEW FULL DETAILS) ── */}
            {activeTab === "life_areas" && (
              <div className="space-y-4 animate-fade-in" ref={detailsContainerRef}>
                {/* 1. Active Section Detailed Card */}
                {localizedActiveSection ? (
                  <div className="p-4 sm:p-5 rounded-xl bg-white border border-[#ebdcb9] shadow-xs space-y-4">
                    {/* Header with Title and Evidence Badge */}
                    <div className="flex items-start justify-between border-b border-slate-100 pb-3">
                      <div>
                        <h2 className="font-serif font-bold text-base sm:text-lg text-[#800020]">
                          {localizedActiveSection.title}
                        </h2>
                        <span className="text-[11px] text-slate-500 font-medium">
                          {ui.parashariSystem}
                        </span>
                      </div>
                      <span
                        className={`text-xs font-bold uppercase px-2.5 py-1 rounded-full ${
                          localizedActiveSection.evidence_level === "Convergent"
                            ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                            : localizedActiveSection.evidence_level === "Moderate"
                            ? "bg-amber-100 text-amber-800 border border-amber-200"
                            : "bg-slate-100 text-slate-700 border border-slate-200"
                        }`}
                      >
                        {EVIDENCE_LEVEL_MAP[selectedLang]?.[localizedActiveSection.evidence_level] || localizedActiveSection.evidence_level} ({LEAN_MAP[selectedLang]?.[localizedActiveSection.lean?.toLowerCase()] || localizedActiveSection.lean})
                      </span>
                    </div>

                    {/* Astrological Grounding Facts Box: Simple vs Advanced Mode (Section 20) with ENLARGED FONT SIZE */}
                    {(localizedActiveSection.supporting_factors?.length ||
                      localizedActiveSection.challenging_factors?.length) ? (
                      <div className="p-4 sm:p-5 rounded-xl bg-amber-50/60 border border-amber-200/90 text-sm space-y-4 shadow-2xs">
                        <div className="flex items-center justify-between border-b border-amber-200/60 pb-2.5">
                          <span className="text-xs sm:text-sm font-bold uppercase tracking-wider text-amber-950 block">
                            {explanationMode === "simple"
                              ? (selectedLang === "bn" ? "অনুকূল ও পরিমার্জক গ্রহীয় সূত্র (সহজ বিশ্লেষণ)" : selectedLang === "hi" ? "अनुकूल एवं परिमार्जक ग्रह योग (सरल व्याख्या)" : "Astrological Factors & Symbolic Indications")
                              : "Astrological Grounding Facts & Lord Placements"}
                          </span>
                          <span className="text-xs text-slate-600 font-medium italic">
                            {explanationMode === "simple"
                              ? selectedLang === "bn" ? "সহজ বিশ্লেষণ (সাধারণ)" : selectedLang === "hi" ? "सरल व्याख्या" : "Layperson Mode"
                              : "Astrologer Technical Mode"}
                          </span>
                        </div>

                        {/* Supporting Factors */}
                        {localizedActiveSection.supporting_factors.length > 0 && (
                          <div>
                            <span className="font-bold text-emerald-900 block text-xs sm:text-sm mb-2">
                              {ui.supportingFactors}:
                            </span>
                            <ul className="space-y-2 text-slate-800">
                              {localizedActiveSection.supporting_factors.slice(0, 3).map((sf, idx) => {
                                const simpleText =
                                  sf.simple_explanation?.[selectedLang] ||
                                  explainRuleClient(sf.rule_id, selectedLang) ||
                                  cleanRuleText(sf.interpretation);

                                return (
                                  <li key={idx} className="flex items-start gap-2.5 bg-white/95 p-3 sm:p-3.5 rounded-xl border border-emerald-100/90 shadow-2xs">
                                    <span className="text-emerald-700 font-bold mt-0.5 text-base">•</span>
                                    <div className="flex-1 space-y-1">
                                      {explanationMode === "simple" ? (
                                        <p className="text-sm sm:text-base text-slate-850 leading-relaxed font-sans">
                                          {simpleText}
                                        </p>
                                      ) : (
                                        <>
                                          <div className="flex items-center gap-2 flex-wrap">
                                            <span className="font-mono text-xs bg-white border border-amber-300 px-2 py-0.5 rounded text-amber-950 font-bold">
                                              {sf.rule_id}
                                            </span>
                                            <span className="text-xs sm:text-sm font-semibold text-slate-850">
                                              {sf.factor || sf.rule_id}
                                            </span>
                                          </div>
                                          <p className="text-xs sm:text-sm text-slate-750 leading-relaxed">
                                            {sf.advanced_explanation?.[selectedLang] || sf.interpretation}
                                          </p>
                                          {sf.why_matters?.[selectedLang] && (
                                            <p className="text-xs text-amber-900 italic">
                                              <strong>Significance:</strong> {sf.why_matters[selectedLang]}
                                            </p>
                                          )}
                                        </>
                                      )}
                                    </div>
                                  </li>
                                );
                              })}
                            </ul>
                          </div>
                        )}

                        {/* Challenging / Modifying Factors */}
                        {localizedActiveSection.challenging_factors.length > 0 && (
                          <div className="pt-3 border-t border-amber-200/60">
                            <span className="font-bold text-amber-950 block text-xs sm:text-sm mb-2">
                              {ui.modifyingFactors}:
                            </span>
                            <ul className="space-y-2 text-slate-800">
                              {localizedActiveSection.challenging_factors.slice(0, 2).map((cf, idx) => {
                                const simpleText =
                                  cf.simple_explanation?.[selectedLang] ||
                                  explainRuleClient(cf.rule_id, selectedLang) ||
                                  cleanRuleText(cf.interpretation);

                                return (
                                  <li key={idx} className="flex items-start gap-2.5 bg-white/95 p-3 sm:p-3.5 rounded-xl border border-amber-200/80 shadow-2xs">
                                    <span className="text-amber-800 font-bold mt-0.5 text-base">•</span>
                                    <div className="flex-1 space-y-1">
                                      {explanationMode === "simple" ? (
                                        <p className="text-sm sm:text-base text-slate-850 leading-relaxed font-sans">
                                          {simpleText}
                                        </p>
                                      ) : (
                                        <>
                                          <div className="flex items-center gap-2 flex-wrap">
                                            <span className="font-mono text-xs bg-white border border-amber-300 px-2 py-0.5 rounded text-amber-950 font-bold">
                                              {cf.rule_id}
                                            </span>
                                            <span className="text-xs sm:text-sm font-semibold text-slate-850">
                                              {cf.factor || cf.rule_id}
                                            </span>
                                          </div>
                                          <p className="text-xs sm:text-sm text-slate-750 leading-relaxed">
                                            {cf.advanced_explanation?.[selectedLang] || cf.interpretation}
                                          </p>
                                          {cf.why_matters?.[selectedLang] && (
                                            <p className="text-xs text-amber-900 italic">
                                              <strong>Significance:</strong> {cf.why_matters[selectedLang]}
                                            </p>
                                          )}
                                        </>
                                      )}
                                    </div>
                                  </li>
                                );
                              })}
                            </ul>
                          </div>
                        )}
                      </div>
                    ) : null}

                    {/* ── SPECIALIZED UPGRADED CAREER REPORT LAYOUT ── */}
                    {localizedActiveSection.topic === "career" && localizedActiveSection.career_analysis ? (
                      <div className="space-y-6 pt-2">
                        {/* A. Career Overview */}
                        <div className="p-4 sm:p-5 rounded-xl bg-gradient-to-br from-amber-50/80 to-rose-50/50 border border-amber-200/90 shadow-2xs space-y-2.5">
                          <h3 className="text-sm sm:text-base font-bold text-[#800020] flex items-center gap-2">
                            <i className="fa-solid fa-briefcase"></i>
                            {selectedLang === "bn" ? "ক. কর্মজীবন ও পেশা — সার্বিক মূল্যায়ন" : selectedLang === "hi" ? "क. आजीविका एवं करियर — समग्र मूल्यांकन" : "A. Career Overview & Vocational Trajectory"}
                          </h3>
                          <p className="text-sm sm:text-base text-slate-800 leading-relaxed font-sans">
                            {localizedActiveSection.career_analysis.overview?.[selectedLang] ||
                              localizedActiveSection.career_analysis.overview?.["en"] ||
                              localizedActiveSection.overview}
                          </p>
                        </div>

                        {/* B. Planetary Placements and Their Practical Meaning */}
                        {localizedActiveSection.career_analysis.placement_cards && (
                          <div className="space-y-3">
                            <h3 className="text-sm sm:text-base font-bold text-[#800020] flex items-center gap-2">
                              <i className="fa-solid fa-compass"></i>
                              {selectedLang === "bn" ? "খ. গ্রহাবস্থান ও ব্যবহারিক পেশাগত তাৎপর্য" : selectedLang === "hi" ? "ख. ग्रह स्थिति एवं व्यावहारिक आजीविका फल" : "B. Planetary Placements & Practical Career Meaning"}
                            </h3>
                            <div className="space-y-3.5">
                              {localizedActiveSection.career_analysis.placement_cards.map((pc, idx) => (
                                <div key={idx} className="p-4 sm:p-5 rounded-xl bg-white border border-[#ebdcb9] shadow-xs space-y-3">
                                  <div className="flex items-center justify-between flex-wrap gap-2 border-b border-slate-100 pb-2">
                                    <h4 className="font-bold text-sm sm:text-base text-[#800020]">
                                      {pc.title?.[selectedLang] || pc.title?.["en"]}
                                    </h4>
                                    <span className={`text-xs px-2.5 py-0.5 rounded-full font-semibold ${
                                      pc.role_type === "direct" ? "bg-emerald-100 text-emerald-800 border border-emerald-200" : "bg-amber-100 text-amber-800 border border-amber-200"
                                    }`}>
                                      {pc.role_type === "direct"
                                        ? (selectedLang === "bn" ? "প্রত্যক্ষ কর্মকারক" : selectedLang === "hi" ? "प्रत्यक्ष आजीविका कारक" : "Direct Career Factor")
                                        : (selectedLang === "bn" ? "সহায়ক/সংশোধনকারী" : selectedLang === "hi" ? "सहायक प्रभाव" : "Supporting Factor")}
                                    </span>
                                  </div>

                                  {/* Meaning */}
                                  <p className="text-xs sm:text-sm text-slate-700 leading-relaxed bg-amber-50/40 p-3 rounded-lg border border-amber-100/70">
                                    {pc.traditional_meaning?.[selectedLang] || pc.traditional_meaning?.["en"]}
                                  </p>

                                  {/* Practical Career Outcomes */}
                                  <div>
                                    <span className="text-xs sm:text-sm font-bold text-emerald-900 block mb-1.5">
                                      {selectedLang === "bn" ? "সম্ভাব্য ব্যবহারিক কর্মজীবনগত ফলাফল:" : selectedLang === "hi" ? "संभावित व्यावहारिक कार्यक्षेत्र फल:" : "Practical Career Implications:"}
                                    </span>
                                    <ul className="space-y-1.5 pl-1">
                                      {(pc.practical_outcomes?.[selectedLang] || pc.practical_outcomes?.["en"] || []).map((out, oIdx) => (
                                        <li key={oIdx} className="flex items-start gap-2 text-xs sm:text-sm text-slate-800">
                                          <span className="text-emerald-700 font-bold mt-0.5">•</span>
                                          <span>{out}</span>
                                        </li>
                                      ))}
                                    </ul>
                                  </div>

                                  {/* Challenges & Limitations */}
                                  {pc.challenges?.[selectedLang]?.length > 0 && (
                                    <div className="pt-2 border-t border-slate-100">
                                      <span className="text-xs sm:text-sm font-bold text-amber-900 block mb-1">
                                        {selectedLang === "bn" ? "সম্ভাব্য চ্যালেঞ্জ বা সীমাবদ্ধতা:" : selectedLang === "hi" ? "संभावित चुनौतियाँ एवं सीमाएँ:" : "Challenges or Limitations:"}
                                      </span>
                                      <ul className="space-y-1 pl-1">
                                        {(pc.challenges[selectedLang] || pc.challenges["en"]).map((ch, cIdx) => (
                                          <li key={cIdx} className="flex items-start gap-2 text-xs sm:text-sm text-slate-700">
                                            <span className="text-amber-700 font-bold mt-0.5">•</span>
                                            <span>{ch}</span>
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}

                                  {/* Modifying factors & non-fatalistic footnote */}
                                  <div className="flex items-center justify-between flex-wrap gap-2 pt-2 border-t border-slate-100 text-[11px] sm:text-xs text-slate-500">
                                    <span>
                                      <strong>{selectedLang === "bn" ? "প্রভাবক:" : selectedLang === "hi" ? "प्रभावक:" : "Modifiers:"}</strong> {pc.modifying_factors?.[selectedLang] || pc.modifying_factors?.["en"]}
                                    </span>
                                    <span className="italic text-amber-900/80">
                                      {pc.non_fatalistic_note?.[selectedLang] || pc.non_fatalistic_note?.["en"]}
                                    </span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* C. Career Strengths & D. Career Challenges */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {/* Strengths */}
                          <div className="p-4 sm:p-5 rounded-xl bg-emerald-50/60 border border-emerald-200/80 shadow-2xs space-y-2">
                            <h4 className="text-xs sm:text-sm font-bold text-emerald-900 flex items-center gap-1.5 uppercase tracking-wider">
                              <i className="fa-solid fa-award text-emerald-700"></i>
                              {selectedLang === "bn" ? "গ. কুণ্ডলী সমর্থিত কর্মদক্ষতা ও শক্তিসমূহ" : selectedLang === "hi" ? "ग. कुंडली समर्थित कार्य क्षमता एवं शक्तियां" : "C. Supported Career Strengths"}
                            </h4>
                            <ul className="space-y-1.5">
                              {(localizedActiveSection.career_analysis.strengths?.[selectedLang] ||
                                localizedActiveSection.career_analysis.strengths?.["en"] || []).map((st, sIdx) => (
                                <li key={sIdx} className="flex items-start gap-2 text-xs sm:text-sm text-slate-800">
                                  <span className="text-emerald-700 font-bold">•</span>
                                  <span>{st}</span>
                                </li>
                              ))}
                            </ul>
                          </div>

                          {/* Challenges */}
                          <div className="p-4 sm:p-5 rounded-xl bg-amber-50/70 border border-amber-200/90 shadow-2xs space-y-2">
                            <h4 className="text-xs sm:text-sm font-bold text-amber-950 flex items-center gap-1.5 uppercase tracking-wider">
                              <i className="fa-solid fa-triangle-exclamation text-amber-700"></i>
                              {selectedLang === "bn" ? "ঘ. সীমাবদ্ধতা ও সতর্কতামূলক দিক" : selectedLang === "hi" ? "घ. सीमाएं एवं सावधानियां" : "D. Career Challenges & Growth Areas"}
                            </h4>
                            <ul className="space-y-1.5">
                              {(localizedActiveSection.career_analysis.challenges?.[selectedLang] ||
                                localizedActiveSection.career_analysis.challenges?.["en"] || []).map((ch, cIdx) => (
                                <li key={cIdx} className="flex items-start gap-2 text-xs sm:text-sm text-slate-800">
                                  <span className="text-amber-800 font-bold">•</span>
                                  <span>{ch}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>

                        {/* E. Employment vs Business Comparison */}
                        {localizedActiveSection.career_analysis.employment_vs_business && (
                          <div className="p-4 sm:p-5 rounded-xl bg-white border border-[#ebdcb9] shadow-xs space-y-3">
                            <h3 className="text-sm sm:text-base font-bold text-[#800020] flex items-center gap-2">
                              <i className="fa-solid fa-scale-balanced"></i>
                              {selectedLang === "bn" ? "ঙ. চাকরি বনাম স্বাধীন ব্যবসা — তুলনামূলক বিচার" : selectedLang === "hi" ? "ङ. नौकरी बनाम स्वतंत्र व्यवसाय — तुलनात्मक विश्लेषण" : "E. Employment vs Business Comparison"}
                            </h3>

                            {/* Verdict Banner */}
                            <div className="p-3.5 rounded-lg bg-amber-100/70 border border-amber-300 text-xs sm:text-sm font-bold text-[#800020]">
                              <i className="fa-solid fa-check-double mr-1.5"></i>
                              {localizedActiveSection.career_analysis.employment_vs_business.verdict?.[selectedLang] ||
                                localizedActiveSection.career_analysis.employment_vs_business.verdict?.["en"]}
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 pt-1">
                              {/* Employment Factors */}
                              <div className="p-3 sm:p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1.5">
                                <span className="font-bold text-xs sm:text-sm text-slate-850 block">
                                  {selectedLang === "bn" ? "চাকরি ও প্রাতিষ্ঠানিক সেবার কারণ:" : selectedLang === "hi" ? "नौकरी एवं सेवा के कारक:" : "Employment & Service Factors:"}
                                </span>
                                <ul className="space-y-1 text-xs sm:text-sm text-slate-750">
                                  {(localizedActiveSection.career_analysis.employment_vs_business.emp_factors?.[selectedLang] || []).map((ef, efIdx) => (
                                    <li key={efIdx} className="flex items-start gap-1.5">
                                      <span className="text-slate-500">•</span>
                                      <span>{ef}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>

                              {/* Business Factors */}
                              <div className="p-3 sm:p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1.5">
                                <span className="font-bold text-xs sm:text-sm text-slate-850 block">
                                  {selectedLang === "bn" ? "স্বাধীন ব্যবসা ও অংশীদারির কারণ:" : selectedLang === "hi" ? "स्वतंत्र व्यवसाय एवं साझेदारी के कारक:" : "Business & Partnership Factors:"}
                                </span>
                                <ul className="space-y-1 text-xs sm:text-sm text-slate-750">
                                  {(localizedActiveSection.career_analysis.employment_vs_business.biz_factors?.[selectedLang] || []).map((bf, bfIdx) => (
                                    <li key={bfIdx} className="flex items-start gap-1.5">
                                      <span className="text-slate-500">•</span>
                                      <span>{bf}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* F. Career Timeline & Timing Opportunities */}
                        {localizedActiveSection.career_analysis.timeline && localizedActiveSection.career_analysis.timeline.length > 0 && (
                          <div className="p-4 sm:p-5 rounded-xl bg-white border border-[#ebdcb9] shadow-xs space-y-3.5">
                            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                              <h3 className="text-sm sm:text-base font-bold text-[#800020] flex items-center gap-2">
                                <i className="fa-solid fa-timeline"></i>
                                {selectedLang === "bn" ? "চ. পেশাগত সময়কাল ও সুযোগের দিগন্ত (বিংশোত্তরী দশাভিত্তিক)" : selectedLang === "hi" ? "च. आजीविका समय चक्र एवं अवसर (विंशोत्तरी दशा आधारित)" : "F. Career Timeline & Timing Windows"}
                              </h3>
                              <span className="text-[11px] text-slate-500 font-medium">
                                {selectedLang === "bn" ? "প্রকৃত জ্যোতিষীয় হিসাব" : "Astronomically Calculated"}
                              </span>
                            </div>

                            <div className="space-y-3">
                              {localizedActiveSection.career_analysis.timeline.map((te, tIdx) => (
                                <div key={tIdx} className="p-3 sm:p-3.5 rounded-xl bg-slate-50/80 border border-slate-200 hover:border-amber-300 transition-colors space-y-1.5">
                                  <div className="flex items-center justify-between flex-wrap gap-2">
                                    <span className="font-bold text-xs sm:text-sm text-[#800020]">
                                      {te.event?.[selectedLang] || te.event?.["en"]}
                                    </span>
                                    <div className="flex items-center gap-2">
                                      <span className="font-mono text-xs font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                                        {te.age_range}
                                      </span>
                                      <span className="text-xs text-slate-600 bg-white px-2 py-0.5 rounded border border-slate-200 font-medium">
                                        {te.period_dates}
                                      </span>
                                    </div>
                                  </div>
                                  <p className="text-xs sm:text-sm text-slate-750 leading-relaxed font-sans">
                                    {te.explanation?.[selectedLang] || te.explanation?.["en"]}
                                  </p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <>
                        {/* Domain Overview (40-70 words) for other domains */}
                        <div>
                          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">
                            {ui.domainOverview}
                          </h4>
                          <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-sans">
                            {localizedActiveSection.overview}
                          </p>
                        </div>

                        {/* Core Themes (3 items) */}
                        {localizedActiveSection.themes && localizedActiveSection.themes.length > 0 && (
                          <div>
                            <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-800 mb-1.5 flex items-center gap-1.5">
                              <i className="fa-solid fa-sparkles text-emerald-600"></i> {ui.coreThemes}
                            </h4>
                            <ul className="space-y-1.5">
                              {localizedActiveSection.themes.slice(0, 3).map((th, idx) => (
                                <li key={idx} className="flex items-start gap-2 text-xs text-slate-700">
                                  <span className="text-emerald-700 font-bold">•</span>
                                  <span>{th}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Mindful Growth Challenges (2 items) */}
                        {localizedActiveSection.challenges && localizedActiveSection.challenges.length > 0 && (
                          <div>
                            <h4 className="text-xs font-bold uppercase tracking-wider text-amber-900 mb-1.5 flex items-center gap-1.5">
                              <i className="fa-solid fa-shield-halved text-amber-700"></i> {ui.growthChallenges}
                            </h4>
                            <ul className="space-y-1.5">
                              {localizedActiveSection.challenges.slice(0, 2).map((ch, idx) => (
                                <li key={idx} className="flex items-start gap-2 text-xs text-slate-700">
                                  <span className="text-amber-700 font-bold">•</span>
                                  <span>{ch}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </>
                    )}

                    {/* Collapsible 6-Point "Why this prediction?" Accordion (Section 20.B) */}
                    <div className="pt-2 border-t border-slate-100">
                      <button
                        onClick={() => toggleWhyThis(`topic-${activeSection?.topic || selectedTopic}`)}
                        className="w-full flex items-center justify-between text-xs font-semibold text-slate-700 p-2.5 rounded-lg bg-amber-50/60 hover:bg-amber-100/60 border border-amber-200 transition-colors"
                      >
                        <span className="flex items-center gap-2">
                          <i className="fa-solid fa-circle-question text-[#800020] text-sm"></i>
                          <span className="font-bold text-[#800020]">{ui.whyThisPrediction}</span>
                        </span>
                        <i
                          className={`fa-solid fa-chevron-down text-[11px] transition-transform ${
                            expandedWhyThis[`topic-${activeSection?.topic || selectedTopic}`] ? "rotate-180" : ""
                          }`}
                        ></i>
                      </button>

                      {expandedWhyThis[`topic-${activeSection?.topic || selectedTopic}`] && (
                        <div className="mt-2.5 p-3.5 bg-[#fffdfa] rounded-xl text-xs text-slate-700 border border-amber-200 shadow-2xs space-y-3 animate-fade-in">
                          {/* 6 Structured Breakdown Points */}
                          <div className="space-y-2">
                            {/* Point 1: Placement Meaning */}
                            <div className="p-2 rounded bg-amber-50/50 border border-amber-100">
                              <span className="font-bold text-[#800020] block text-[11px] mb-0.5">
                                {ui.point1}
                              </span>
                              <p className="text-[11px] text-slate-700 leading-relaxed">
                                {localizedActiveSection.why_this?.placement_meaning?.[selectedLang] ||
                                  localizedActiveSection.why_this?.placement_meaning?.["en"] ||
                                  "Natal planetary alignments establish foundational strengths across pivotal houses."}
                              </p>
                            </div>

                            {/* Point 2: Specific Houses & Planets Involved */}
                            <div className="p-2 rounded bg-amber-50/50 border border-amber-100">
                              <span className="font-bold text-[#800020] block text-[11px] mb-0.5">
                                {ui.point2}
                              </span>
                              <p className="text-[11px] text-slate-700 leading-relaxed font-mono text-[10px]">
                                {localizedActiveSection.why_this?.involved_factors?.[selectedLang] ||
                                  localizedActiveSection.why_this?.involved_factors?.["en"]}
                              </p>
                            </div>

                            {/* Point 3: Life Themes Connected */}
                            <div className="p-2 rounded bg-amber-50/50 border border-amber-100">
                              <span className="font-bold text-[#800020] block text-[11px] mb-0.5">
                                {ui.point3}
                              </span>
                              <p className="text-[11px] text-slate-700 leading-relaxed">
                                {localizedActiveSection.why_this?.life_themes?.[selectedLang] ||
                                  localizedActiveSection.why_this?.life_themes?.["en"]}
                              </p>
                            </div>

                            {/* Point 4: Relevance to this Specific Prediction */}
                            <div className="p-2 rounded bg-amber-50/50 border border-amber-100">
                              <span className="font-bold text-[#800020] block text-[11px] mb-0.5">
                                {ui.point4}
                              </span>
                              <p className="text-[11px] text-slate-700 leading-relaxed">
                                {localizedActiveSection.why_this?.relevance?.[selectedLang] ||
                                  localizedActiveSection.why_this?.relevance?.["en"]}
                              </p>
                            </div>

                            {/* Point 5: Modifying Factors */}
                            <div className="p-2 rounded bg-amber-50/50 border border-amber-100">
                              <span className="font-bold text-[#800020] block text-[11px] mb-0.5">
                                {ui.point5}
                              </span>
                              <p className="text-[11px] text-slate-700 leading-relaxed">
                                {localizedActiveSection.why_this?.modifying_factors?.[selectedLang] ||
                                  localizedActiveSection.why_this?.modifying_factors?.["en"]}
                              </p>
                            </div>

                            {/* Point 6: Synthesis */}
                            <div className="p-2 rounded bg-amber-50/50 border border-amber-100">
                              <span className="font-bold text-[#800020] block text-[11px] mb-0.5">
                                {ui.point6}
                              </span>
                              <p className="text-[11px] text-slate-700 leading-relaxed font-semibold text-emerald-900">
                                {localizedActiveSection.why_this?.synthesis?.[selectedLang] ||
                                  localizedActiveSection.why_this?.synthesis?.["en"]}
                              </p>
                            </div>
                          </div>

                          {/* Rule IDs (shown only in Advanced Mode or collapsed) */}
                          {explanationMode === "advanced" && (
                            <div className="pt-2 border-t border-amber-200/60">
                              <span className="font-semibold block text-[11px] text-slate-700 mb-1">
                                {ui.verifiedBasis}:
                              </span>
                              <div className="flex flex-wrap gap-1">
                                {localizedActiveSection.basis_ids.map((id) => (
                                  <span
                                    key={id}
                                    className="px-1.5 py-0.5 rounded bg-white border border-amber-300 font-mono text-[10px] text-amber-950 font-semibold"
                                  >
                                    {id}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="p-8 text-center text-slate-400">
                    Please select a topic heading from the pills above.
                  </div>
                )}

                {/* 2. Grid of other Life Area Cards (Clicking any card heading switches to it) */}
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                    {ui.allLifeDomains}
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {(predictionReport?.sections || []).map((sec) => {
                      const isSelected =
                        sec.topic.toLowerCase() === selectedTopic.toLowerCase() ||
                        sec.title.toLowerCase().includes(selectedTopic.toLowerCase());
                      const tr = sec.translations?.[selectedLang];
                      const cardTitle = tr?.title || sec.title;
                      const cardOverview = tr?.overview || sec.overview || sec.summary;

                      return (
                        <div
                          key={sec.topic}
                          onClick={() => handleSelectTopic(sec.topic)}
                          className={`p-3 rounded-xl border cursor-pointer transition-all flex flex-col justify-between ${
                            isSelected
                              ? "bg-amber-50/60 border-[#800020] shadow-xs ring-1 ring-[#800020]"
                              : "bg-white hover:border-amber-300 border-slate-200 shadow-2xs"
                          }`}
                        >
                          <div>
                            <div className="flex items-center justify-between mb-1.5">
                              <h4 className="font-serif font-bold text-xs text-[#800020] hover:underline">
                                {cardTitle}
                              </h4>
                              <span
                                className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded ${
                                  sec.evidence_level === "Convergent"
                                    ? "bg-emerald-100 text-emerald-800"
                                    : sec.evidence_level === "Moderate"
                                    ? "bg-amber-100 text-amber-800"
                                    : "bg-slate-100 text-slate-700"
                                }`}
                              >
                                {sec.evidence_level}
                              </span>
                            </div>
                            <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">
                              {cardOverview}
                            </p>
                          </div>

                          <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-[#800020] font-semibold">
                            <span>{isSelected ? ui.activeView : ui.clickToView}</span>
                            <span>&rarr;</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}

            {/* ── TAB: OVERVIEW ── */}
            {activeTab === "overview" && (
              <div className="space-y-4 animate-fade-in">
                {/* Executive Overview */}
                <div className="p-4 rounded-xl bg-gradient-to-br from-[#fffdfa] to-[#fcf7ee] border border-[#ebdcb9]">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-[#800020] flex items-center gap-1.5">
                      <i className="fa-solid fa-scroll"></i> {ui.executiveOverview}
                    </span>
                    {predictionReport?.chart_overview && (
                      <span className="text-[11px] font-semibold text-slate-600">
                        {predictionReport.chart_overview.lagna_sign_name} Lagna &bull;{" "}
                        {predictionReport.chart_overview.rashi_sign_name} Moon
                      </span>
                    )}
                  </div>
                  <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-sans">
                    {localizedExecutiveOverview}
                  </p>
                </div>

                {/* Current Dasha Strip */}
                {currentDasha?.md && (
                  <div className="p-3 rounded-lg bg-amber-50/60 border border-amber-200 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-amber-200 text-amber-900 flex items-center justify-center font-bold text-[10px]">
                        ⏳
                      </span>
                      <div>
                        <span className="font-bold text-amber-950">{ui.activePeriods}: </span>
                        <span className="text-slate-700">
                          <strong>{ui.mahadasha}:</strong> {currentDasha.md.lord} (until {currentDasha.md.end}) &bull;{" "}
                          <strong>{ui.antardasha}:</strong> {currentDasha.ad?.lord || "Active"}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => setActiveTab("current_period")}
                      className="text-[11px] font-bold text-[#800020] hover:underline"
                    >
                      Details &rarr;
                    </button>
                  </div>
                )}

                {/* Insight Chips */}
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                    {ui.allLifeDomains}
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {(predictionReport?.sections || []).map((sec) => {
                      const tr = sec.translations?.[selectedLang];
                      const cardTitle = tr?.title || sec.title;
                      const cardOverview = tr?.overview || sec.overview || sec.summary;

                      return (
                        <div
                          key={sec.topic}
                          onClick={() => handleSelectTopic(sec.topic)}
                          className="p-3 rounded-lg bg-white border border-slate-200 hover:border-amber-400 cursor-pointer transition-colors shadow-2xs flex flex-col justify-between"
                        >
                          <div>
                            <div className="flex items-center justify-between mb-1">
                              <h4 className="font-serif font-bold text-xs text-[#800020] hover:underline">
                                {cardTitle}
                              </h4>
                              <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-slate-100 text-slate-700">
                                {sec.evidence_level}
                              </span>
                            </div>
                            <p className="text-xs text-slate-600 line-clamp-2 leading-snug">
                              {cardOverview}
                            </p>
                          </div>
                          <div className="mt-2 pt-2 border-t border-slate-100 text-[11px] text-amber-800 font-semibold flex items-center justify-between">
                            <span>{ui.clickToView}</span>
                            <span>&rarr;</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}

            {/* ── TAB: CURRENT PERIOD ── */}
            {activeTab === "current_period" && (
              <div className="space-y-4 animate-fade-in">
                <div className="p-4 rounded-xl bg-gradient-to-br from-amber-50 to-orange-50/40 border border-amber-200">
                  <h3 className="font-serif font-bold text-base text-amber-950 mb-1 flex items-center gap-2">
                    <span>⏳</span> {ui.activePeriods}
                  </h3>
                  <p className="text-xs text-slate-600 mb-3">
                    Planetary timing modulates natal potential into concrete life experiences across specific cycles.
                  </p>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {currentDasha?.md && (
                      <div className="p-3 rounded-lg bg-white border border-amber-200 shadow-2xs">
                        <span className="text-[10px] font-bold uppercase text-amber-800 tracking-wider block">
                          {ui.mahadasha}
                        </span>
                        <span className="font-serif font-bold text-base text-slate-800 block my-0.5">
                          {currentDasha.md.lord} Mahadasha
                        </span>
                        <span className="text-xs text-slate-500">
                          From {currentDasha.md.start} to {currentDasha.md.end}
                        </span>
                      </div>
                    )}

                    {currentDasha?.ad && (
                      <div className="p-3 rounded-lg bg-white border border-amber-200 shadow-2xs">
                        <span className="text-[10px] font-bold uppercase text-amber-800 tracking-wider block">
                          {ui.antardasha}
                        </span>
                        <span className="font-serif font-bold text-base text-slate-800 block my-0.5">
                          {currentDasha.ad.lord} Antardasha
                        </span>
                        <span className="text-xs text-slate-500">
                          From {currentDasha.ad.start} to {currentDasha.ad.end}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-white border border-slate-200">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600 mb-2.5">
                    3 Active Themes for the Current Period
                  </h4>
                  <ul className="space-y-2">
                    <li className="flex items-start gap-2 text-xs text-slate-700">
                      <span className="text-[#800020] font-bold">1.</span>
                      <span>
                        Consolidation of vocational agency and active application of specialized professional skills.
                      </span>
                    </li>
                    <li className="flex items-start gap-2 text-xs text-slate-700">
                      <span className="text-[#800020] font-bold">2.</span>
                      <span>
                        Disciplined stewardship over financial resources and long-term commitments.
                      </span>
                    </li>
                    <li className="flex items-start gap-2 text-xs text-slate-700">
                      <span className="text-[#800020] font-bold">3.</span>
                      <span>
                        Harmonizing relationship commitments with personal growth and mindful ethical conduct.
                      </span>
                    </li>
                  </ul>

                  {currentDasha?.ad && (
                    <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                      <span className="text-slate-600">
                        Next Antardasha Transition: <strong>{currentDasha.ad.end}</strong>
                      </span>
                      <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-900 font-semibold text-[11px]">
                        Scheduled Cycle Shift
                      </span>
                    </div>
                  )}
                </div>

                <div className="pt-2">
                  <button
                    onClick={() => setShowPratyantardasha(!showPratyantardasha)}
                    className="text-xs font-semibold text-slate-600 hover:text-slate-900 flex items-center gap-1.5"
                  >
                    <i className={`fa-solid ${showPratyantardasha ? "fa-eye-slash" : "fa-eye"}`}></i>
                    {showPratyantardasha ? ui.hidePratyantardasha : ui.pratyantardasha}
                  </button>

                  {showPratyantardasha && (
                    <div className="mt-3 p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-600 animate-fade-in">
                      <p className="font-medium text-slate-700 mb-2">Pratyantardasha Sub-Cycles:</p>
                      <div className="space-y-1 text-[11px]">
                        <div>• Micro-period modulated by the current sub-lord.</div>
                        <div>• Activates rapid turns in day-to-day matters and mental responsiveness.</div>
                        <div>• Calibrated with Lahiri Ayanamsa whole-sign progressions.</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* ── TAB: ADVANCED ── */}
            {activeTab === "advanced" && (
              <div className="space-y-4 animate-fade-in">
                <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <div>
                    <h4 className="font-bold text-xs text-slate-800">Astrologer Manual Review &amp; Edits</h4>
                    <p className="text-[11px] text-slate-500">
                      Customize prediction text without altering astronomical calculations.
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setEditingTopic(selectedTopic);
                      setEditContent(activeSection?.prediction || activeSection?.overview || "");
                      setIsEditDrawerOpen(true);
                    }}
                    className="px-3 py-1.5 rounded-lg bg-amber-800 hover:bg-amber-900 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors"
                  >
                    <i className="fa-solid fa-pen-to-square"></i> Edit Section
                  </button>
                </div>

                {/* Verified Yogas Table */}
                {predictionReport?.yoga_trace && predictionReport.yoga_trace.length > 0 && (
                  <div className="p-4 rounded-xl bg-white border border-slate-200">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-serif font-bold text-xs uppercase tracking-wider text-[#800020]">
                        Verified Classical Yogas ({predictionReport.yoga_trace.length})
                      </h4>
                      <span className="text-[10px] font-mono text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded">
                        Condition Checks Passed
                      </span>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead>
                          <tr className="border-b border-slate-200 text-slate-500 text-[11px]">
                            <th className="py-1.5 pr-2">Yoga</th>
                            <th className="py-1.5 px-2">Planets</th>
                            <th className="py-1.5 px-2">Houses</th>
                            <th className="py-1.5 pl-2">Conditions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {predictionReport.yoga_trace.map((y, idx) => (
                            <tr key={idx} className="border-b border-slate-100 text-slate-700">
                              <td className="py-1.5 pr-2 font-semibold text-[#800020]">{y.name}</td>
                              <td className="py-1.5 px-2">{y.planets?.join(", ")}</td>
                              <td className="py-1.5 px-2">{y.houses?.join(", ")}</td>
                              <td className="py-1.5 pl-2 text-[11px] text-emerald-800">
                                {y.conditions?.map((c: any) => c.cond).join("; ") || "Verified"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Evidence Matrix */}
                <div className="p-4 rounded-xl bg-white border border-slate-200">
                  <h4 className="font-serif font-bold text-xs uppercase tracking-wider text-slate-600 mb-2">
                    Evidence Matrix &amp; Section Status
                  </h4>
                  <div className="space-y-2">
                    {(predictionReport?.sections || []).map((sec) => (
                      <div
                        key={sec.topic}
                        className="p-2 rounded bg-slate-50 border border-slate-200 flex items-center justify-between text-xs"
                      >
                        <div>
                          <span className="font-bold text-slate-800">{sec.title}</span> &bull;{" "}
                          <span className="text-slate-500">{sec.evidence_level} ({sec.lean})</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded bg-white border border-slate-300 font-mono text-[10px]">
                            {sec.status}
                          </span>
                          <span className="text-[11px] text-slate-400">
                            {(sec.basis_ids || sec.rule_ids || []).length} basis factors
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>
      </main>

      {/* ── Edit Section Drawer / Modal ── */}
      {isEditDrawerOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white border-2 border-[#ebdcb9] rounded-2xl w-full max-w-xl p-5 shadow-2xl flex flex-col gap-3 animate-scale-up">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <div>
                <h3 className="font-serif font-bold text-base text-[#800020]">Edit Section Content</h3>
                <span className="text-xs text-slate-500">Refine prediction wording for this report</span>
              </div>
              <button
                onClick={() => setIsEditDrawerOpen(false)}
                className="w-7 h-7 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-500 font-bold flex items-center justify-center text-xs"
              >
                ✕
              </button>
            </div>

            <div className="flex items-center gap-2 text-xs">
              <span className="font-semibold text-slate-600">Select Section:</span>
              <select
                value={editingTopic}
                onChange={(e) => {
                  const t = e.target.value;
                  setEditingTopic(t);
                  const s = predictionReport?.sections.find((x) => x.topic === t);
                  setEditContent(s?.prediction || s?.overview || "");
                }}
                className="py-1 px-2 border border-slate-200 rounded text-xs"
              >
                {(predictionReport?.sections || []).map((sec) => (
                  <option key={sec.topic} value={sec.topic}>
                    {sec.title}
                  </option>
                ))}
              </select>
            </div>

            <textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              rows={8}
              className="w-full p-3 border border-slate-200 rounded-lg text-xs leading-relaxed font-sans focus:outline-none focus:border-amber-400"
              placeholder="Enter astrologer manual edits..."
            />

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                onClick={() => setIsEditDrawerOpen(false)}
                className="px-3 py-1.5 rounded-lg border border-slate-200 text-slate-600 text-xs font-semibold hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveSectionEdit}
                disabled={savingSection}
                className="px-4 py-1.5 rounded-lg bg-[#800020] text-white text-xs font-semibold hover:bg-[#600018] flex items-center gap-1.5 shadow-sm disabled:opacity-50"
              >
                {savingSection ? <LoadingSpinner /> : <i className="fa-solid fa-floppy-disk"></i>}
                Save Manual Edits
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── AI Settings Modal ── */}
      {aiSettingsOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white border-2 border-[#ebdcb9] rounded-2xl w-full max-w-md p-5 shadow-2xl flex flex-col gap-4 animate-scale-up">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <div className="flex items-center gap-2">
                <span className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-700 flex items-center justify-center text-sm">
                  <i className="fa-solid fa-microchip"></i>
                </span>
                <div>
                  <h3 className="font-serif font-bold text-sm text-slate-800">AI Consistency Engine Settings</h3>
                  <p className="text-[10px] text-slate-500">Select free tier provider or custom API endpoint</p>
                </div>
              </div>
              <button
                onClick={() => setAiSettingsOpen(false)}
                className="w-6 h-6 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-500 flex items-center justify-center text-xs"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">AI Provider</label>
                <select
                  value={selectedProvider}
                  onChange={(e) => {
                    const p = e.target.value;
                    setSelectedProvider(p);
                    if (p === "groq") setSelectedModel("llama-3.3-70b-versatile");
                    else if (p === "gemini") setSelectedModel("gemini-1.5-flash");
                    else if (p === "openrouter") setSelectedModel("meta-llama/llama-3.3-70b-instruct:free");
                  }}
                  className="w-full p-2 border border-slate-200 rounded-lg text-xs bg-slate-50 focus:bg-white"
                >
                  <option value="groq">Groq Cloud (Free Tier - Ultra Fast LLaMA 3.3)</option>
                  <option value="gemini">Google Gemini (Free Tier - gemini-1.5-flash)</option>
                  <option value="openrouter">OpenRouter (Free Tier Models)</option>
                  <option value="custom">Custom / Local OpenAI-Compatible</option>
                </select>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Model Selection</label>
                <input
                  type="text"
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full p-2 border border-slate-200 rounded-lg text-xs"
                  placeholder="e.g. llama-3.3-70b-versatile"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">API Key (Optional override)</label>
                <input
                  type="password"
                  value={apiKeyInput}
                  onChange={(e) => setApiKeyInput(e.target.value)}
                  className="w-full p-2 border border-slate-200 rounded-lg text-xs font-mono"
                  placeholder="Leave empty to use server environment key"
                />
              </div>

              <div className="p-2.5 rounded bg-amber-50 text-[11px] text-amber-900 border border-amber-200">
                <strong>Privacy Guarantee:</strong> Only anonymized astrological factors and rule IDs are audited. No client name, coordinates, or birth specifics are transmitted.
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                onClick={() => setAiSettingsOpen(false)}
                className="px-3 py-1.5 rounded-lg border border-slate-200 text-slate-600 text-xs font-semibold hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveAiSettings}
                className="px-4 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700 shadow-sm"
              >
                Save Settings
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── About Modal ── */}
      <AboutModal isOpen={isAboutOpen} onClose={() => setIsAboutOpen(false)} />
    </div>
  );
}
