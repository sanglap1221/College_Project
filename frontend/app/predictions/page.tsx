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

export default function PredictionsPage() {
  const router = useRouter();
  const { user, isAdmin, logout } = useAuth();

  // Core Form & Prediction States
  const [formValue, setFormValue] = useState<ReportInput>(initialFormValue);
  const [showBirthForm, setShowBirthForm] = useState(false);
  const [predictionReport, setPredictionReport] = useState<PredictionReport | null>(null);

  // Left Column: "জীবন জিজ্ঞাসা" Kundli Chart PDF & Preview States
  const [chartPdfUrl, setChartPdfUrl] = useState<string>("");
  const [chartDownloadUrl, setChartDownloadUrl] = useState<string>("");
  const [chartLanguage, setChartLanguage] = useState<string>("bn");
  const [chartLoading, setChartLoading] = useState<boolean>(false);
  const chartIframeRef = useRef<HTMLIFrameElement | null>(null);

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

  // ── 1. Load Kundli Chart Sheet ("জীবন জিজ্ঞাসা") ──
  const loadChartReport = useCallback(
    async (input: ReportInput, lang: string = "bn") => {
      try {
        setChartLoading(true);
        const calc = await calculateReport({ ...input, language: lang });
        const pdfRes = await renderPdf(calc);
        setChartPdfUrl(pdfRes.preview_url);
        setChartDownloadUrl(pdfRes.compiled_pdf_url);
      } catch (err: any) {
        console.warn("Could not compile Kundli Chart preview:", err);
      } finally {
        setChartLoading(false);
      }
    },
    []
  );

  // ── 2. Generate Natal Predictions ──
  const handleGeneratePredictions = useCallback(
    async (input: ReportInput, force: boolean = false) => {
      if (!input.name || !input.dob || !input.time || !input.place) {
        setShowBirthForm(true);
        return;
      }

      setLoading(true);
      setError("");
      setSuccessMessage("");

      try {
        const reportId = predictionReport?.report_id || `pred-${Date.now().toString(36)}`;
        const report = await generatePredictions({
          report_id: reportId,
          customer_data: input,
          use_ai: useAi,
          provider: selectedProvider,
          model: selectedModel,
          force_regenerate: force,
          language: input.language || chartLanguage || "en",
        });

        setPredictionReport(report);
        setShowBirthForm(false);
        setSuccessMessage("Predictions generated successfully with Jyotish Rulebook v2.0!");
        setTimeout(() => setSuccessMessage(""), 4000);
      } catch (err: any) {
        console.error("Prediction generation error:", err);
        setError(err.message || "Failed to generate predictions.");
      } finally {
        setLoading(false);
      }
    },
    [chartLanguage, predictionReport?.report_id, selectedModel, selectedProvider, useAi]
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
          const lang = parsed.language || "bn";
          setChartLanguage(lang);

          // Load Kundli Chart ("জীবন জিজ্ঞাসা") in Left Column
          loadChartReport(parsed, lang);

          // Generate Predictions in Right Column
          handleGeneratePredictions(parsed, false);
        } catch (e) {
          console.error("Error reading stored prediction details:", e);
        }
      } else {
        setShowBirthForm(true);
      }
    }
  }, [handleGeneratePredictions, loadChartReport]);

  // ── 4. Switch Chart Language (বাংলা / English / हिंदी) ──
  const handleChartLanguageChange = (newLang: string) => {
    setChartLanguage(newLang);
    const updated = { ...formValue, language: newLang };
    setFormValue(updated);
    loadChartReport(updated, newLang);
    if (predictionReport) {
      handleGeneratePredictions(updated, true);
    }
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
    <div className="h-screen w-full flex flex-col font-sans bg-[#fcfbf7] text-slate-800 overflow-hidden">
      {/* ── Top Header Navigation Bar ── */}
      <header className="h-14 shrink-0 bg-white/95 backdrop-blur-md border-b border-[#ebdcb9] z-30 shadow-2xs flex items-center px-4">
        <div className="max-w-7xl mx-auto w-full flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push("/create-report")}
              className="w-8 h-8 rounded-full bg-amber-50 hover:bg-amber-100 flex items-center justify-center text-amber-900 transition-colors"
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
            <button
              onClick={() => router.push("/create-report")}
              className="px-3 py-1.5 rounded-lg border border-[#ebdcb9] hover:bg-amber-50 text-amber-900 text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-2xs"
            >
              <i className="fa-solid fa-chart-pie text-xs"></i> Chart Sheet
            </button>

            <button
              onClick={() => setAiSettingsOpen(true)}
              className="px-3 py-1.5 rounded-lg bg-indigo-50 border border-indigo-200 hover:bg-indigo-100 text-indigo-900 text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <i className="fa-solid fa-microchip text-xs"></i> AI Settings
            </button>

            <button
              onClick={() => setIsAboutOpen(true)}
              className="px-2.5 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-medium hidden sm:flex items-center gap-1"
            >
              <i className="fa-solid fa-circle-info text-xs"></i> About
            </button>

            {isAdmin && (
              <Link
                href="/admin"
                className="px-2.5 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-medium flex items-center gap-1"
              >
                <i className="fa-solid fa-shield text-xs"></i> Admin
              </Link>
            )}

            <button
              onClick={logout}
              className="px-2.5 py-1.5 rounded-lg border border-red-200 text-red-700 hover:bg-red-50 text-xs font-medium flex items-center gap-1 transition-colors"
            >
              <i className="fa-solid fa-arrow-right-from-bracket text-xs"></i> Logout
            </button>
          </div>
        </div>
      </header>

      {/* ── Status Alerts ── */}
      {error && (
        <div className="shrink-0 max-w-7xl mx-auto w-full px-4 pt-2">
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
        <div className="shrink-0 max-w-7xl mx-auto w-full px-4 pt-2">
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

      {/* ── Main Workspace: 2 Equal, Responsive, Contained Columns ── */}
      <main className="flex-1 max-w-7xl mx-auto w-full p-3 grid grid-cols-12 gap-4 min-h-0 overflow-hidden">
        {/* ════════════ LEFT COLUMN: "জীবন জিজ্ঞাসা" KUNDLI CHART PDF PREVIEW (6 Cols) ════════════ */}
        <section className="col-span-12 lg:col-span-6 h-full flex flex-col min-h-0 overflow-hidden bg-white border border-[#ebdcb9] rounded-xl shadow-2xs">
          {/* Header Bar for Kundli Chart */}
          <div className="shrink-0 px-3 py-2 bg-[#fffdfa] border-b border-[#ebdcb9] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <i className="fa-solid fa-file-pdf text-[#800020] text-sm"></i>
              <span className="font-serif font-bold text-xs text-slate-800">
                জীবন জিজ্ঞাসা — Kundli Birth Chart
              </span>
            </div>

            <div className="flex items-center gap-2">
              {/* Language Selector */}
              <div className="relative">
                <select
                  value={chartLanguage}
                  onChange={(e) => handleChartLanguageChange(e.target.value)}
                  className="rounded-lg pl-2.5 pr-6 py-1 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 appearance-none cursor-pointer outline-none shadow-2xs"
                >
                  <option value="bn">বাংলা (Bengali)</option>
                  <option value="en">English</option>
                  <option value="hi">हिंदी (Hindi)</option>
                </select>
                <span className="absolute inset-y-0 right-2 flex items-center pointer-events-none text-slate-400 text-[9px]">
                  <i className="fa-solid fa-chevron-down"></i>
                </span>
              </div>

              {/* Open in new tab */}
              {chartPdfUrl && (
                <a
                  href={chartDownloadUrl || chartPdfUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="px-2.5 py-1 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 rounded-lg flex items-center gap-1 shadow-2xs transition-colors"
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

          {/* Kundli Chart Preview Frame */}
          <div className="flex-1 min-h-0 bg-[#f8fafc] relative overflow-hidden flex items-center justify-center">
            {chartLoading && (
              <div className="absolute inset-0 bg-white/80 backdrop-blur-xs flex flex-col items-center justify-center gap-2 z-10 text-slate-600">
                <LoadingSpinner />
                <span className="text-xs font-medium">Rendering Kundli Birth Chart...</span>
              </div>
            )}

            {chartPdfUrl ? (
              <iframe
                ref={chartIframeRef}
                src={chartPdfUrl}
                className="w-full h-full border-0 bg-white"
                title="Kundli Birth Chart — জীবন জিজ্ঞাসা"
              />
            ) : (
              <div className="p-8 text-center text-slate-400 flex flex-col items-center gap-2">
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
        <section className="col-span-12 lg:col-span-6 h-full flex flex-col min-h-0 overflow-hidden bg-white border border-[#ebdcb9] rounded-xl shadow-2xs">
          {/* Top Prediction Controls Toolbar */}
          <div className="shrink-0 px-3 py-2 bg-[#fffdfa] border-b border-[#ebdcb9] flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="font-serif font-bold text-xs text-[#800020] flex items-center gap-1.5">
                <i className="fa-solid fa-wand-magic-sparkles"></i> Predictions Workspace
              </span>
              <button
                onClick={() => setShowBirthForm(!showBirthForm)}
                className="text-[11px] text-amber-800 hover:underline flex items-center gap-1 font-sans"
              >
                <i className="fa-solid fa-id-card"></i> {showBirthForm ? "Hide Details" : "Edit Client"}
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
                onClick={() => handleGeneratePredictions(formValue, true)}
                disabled={loading}
                className="px-3 py-1 rounded-lg bg-[#800020] hover:bg-[#600018] text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-2xs disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <LoadingSpinner /> Generating...
                  </>
                ) : (
                  <>
                    <i className="fa-solid fa-rotate text-xs"></i> Regenerate
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
                  handleGeneratePredictions(formValue, true);
                }}
                loading={loading}
              />
            </div>
          )}

          {/* View Mode Tabs (Life Areas | Overview | Current Period | Advanced) */}
          <div className="shrink-0 flex items-center justify-between border-b border-slate-200 bg-white px-3 pt-1.5">
            <div className="flex items-center gap-1">
              {[
                { id: "life_areas", label: "Life Areas", icon: "fa-layer-group" },
                { id: "overview", label: "Overview", icon: "fa-compass" },
                { id: "current_period", label: "Current Period", icon: "fa-clock" },
                { id: "advanced", label: "Advanced", icon: "fa-code-branch" },
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
                    <span>{sec.title}</span>
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
                {activeSection ? (
                  <div className="p-4 sm:p-5 rounded-xl bg-white border border-[#ebdcb9] shadow-xs space-y-4">
                    {/* Header with Title and Evidence Badge */}
                    <div className="flex items-start justify-between border-b border-slate-100 pb-3">
                      <div>
                        <h2 className="font-serif font-bold text-base sm:text-lg text-[#800020]">
                          {activeSection.title}
                        </h2>
                        <span className="text-[11px] text-slate-500 font-medium">
                          Natal Astrological Analysis &bull; Whole Sign Vedic Parashari
                        </span>
                      </div>
                      <span
                        className={`text-xs font-bold uppercase px-2.5 py-1 rounded-full ${
                          activeSection.evidence_level === "Convergent"
                            ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                            : activeSection.evidence_level === "Moderate"
                            ? "bg-amber-100 text-amber-800 border border-amber-200"
                            : "bg-slate-100 text-slate-700 border border-slate-200"
                        }`}
                      >
                        {activeSection.evidence_level} ({activeSection.lean})
                      </span>
                    </div>

                    {/* Astrological Grounding Facts Box */}
                    {(activeSection.supporting_factors?.length || activeSection.challenging_factors?.length) ? (
                      <div className="p-3 rounded-lg bg-amber-50/40 border border-amber-200 text-xs space-y-2">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-amber-900 block">
                          Astrological Grounding Facts &amp; Lord Placements
                        </span>

                        {activeSection.supporting_factors && activeSection.supporting_factors.length > 0 && (
                          <div>
                            <span className="font-semibold text-emerald-800 block text-[11px] mb-0.5">
                              Supporting Factors:
                            </span>
                            <ul className="space-y-1 text-slate-700">
                              {activeSection.supporting_factors.slice(0, 3).map((sf, idx) => (
                                <li key={idx} className="flex items-start gap-1.5">
                                  <span className="text-emerald-700 font-bold">•</span>
                                  <span>
                                    {sf.interpretation}{" "}
                                    <span className="font-mono text-[10px] bg-white border border-amber-300 px-1 rounded text-amber-950 font-semibold">
                                      {sf.rule_id}
                                    </span>
                                  </span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {activeSection.challenging_factors && activeSection.challenging_factors.length > 0 && (
                          <div className="pt-1 border-t border-amber-200/50">
                            <span className="font-semibold text-amber-900 block text-[11px] mb-0.5">
                              Modifying / Challenging Factors:
                            </span>
                            <ul className="space-y-1 text-slate-700">
                              {activeSection.challenging_factors.slice(0, 2).map((cf, idx) => (
                                <li key={idx} className="flex items-start gap-1.5">
                                  <span className="text-amber-800 font-bold">•</span>
                                  <span>
                                    {cf.interpretation}{" "}
                                    <span className="font-mono text-[10px] bg-white border border-amber-300 px-1 rounded text-amber-950 font-semibold">
                                      {cf.rule_id}
                                    </span>
                                  </span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ) : null}

                    {/* Domain Overview (40-70 words) */}
                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">
                        Domain Synthesis &amp; Overview
                      </h4>
                      <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-sans">
                        {activeSection.overview || activeSection.summary}
                      </p>
                    </div>

                    {/* Core Themes (3 items) */}
                    {activeSection.themes && activeSection.themes.length > 0 && (
                      <div>
                        <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-800 mb-1.5 flex items-center gap-1.5">
                          <i className="fa-solid fa-sparkles text-emerald-600"></i> Core Symbolic Themes
                        </h4>
                        <ul className="space-y-1.5">
                          {activeSection.themes.slice(0, 3).map((th, idx) => (
                            <li key={idx} className="flex items-start gap-2 text-xs text-slate-700">
                              <span className="text-emerald-700 font-bold">•</span>
                              <span>{th}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Mindful Growth Challenges (2 items) */}
                    {activeSection.challenges && activeSection.challenges.length > 0 && (
                      <div>
                        <h4 className="text-xs font-bold uppercase tracking-wider text-amber-900 mb-1.5 flex items-center gap-1.5">
                          <i className="fa-solid fa-shield-halved text-amber-700"></i> Mindful Growth Challenges
                        </h4>
                        <ul className="space-y-1.5">
                          {activeSection.challenges.slice(0, 2).map((ch, idx) => (
                            <li key={idx} className="flex items-start gap-2 text-xs text-slate-700">
                              <span className="text-amber-700 font-bold">•</span>
                              <span>{ch}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Collapsible Why This Accordion */}
                    <div className="pt-2 border-t border-slate-100">
                      <button
                        onClick={() => toggleWhyThis(`topic-${activeSection.topic}`)}
                        className="w-full flex items-center justify-between text-xs font-semibold text-slate-700 p-2 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors"
                      >
                        <span className="flex items-center gap-1.5">
                          <i className="fa-solid fa-circle-info text-amber-800"></i>
                          Why this? (Parashari Evidence &amp; Rule Basis)
                        </span>
                        <i
                          className={`fa-solid fa-chevron-down text-[11px] transition-transform ${
                            expandedWhyThis[`topic-${activeSection.topic}`] ? "rotate-180" : ""
                          }`}
                        ></i>
                      </button>

                      {expandedWhyThis[`topic-${activeSection.topic}`] && (
                        <div className="mt-2 p-3 bg-amber-50/50 rounded-lg text-xs text-slate-700 border border-amber-200/60 space-y-2 animate-fade-in">
                          <div className="flex items-center justify-between">
                            <span>
                              <strong>Evidence Level:</strong> {activeSection.evidence_level}
                            </span>
                            <span>
                              <strong>Lean:</strong> {activeSection.lean}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-600">{activeSection.explanation}</p>
                          <div>
                            <span className="font-semibold block text-[11px] text-slate-700 mb-1">
                              Verified Basis Rule IDs:
                            </span>
                            <div className="flex flex-wrap gap-1">
                              {(activeSection.basis_ids || activeSection.rule_ids || []).map((id) => (
                                <span
                                  key={id}
                                  className="px-1.5 py-0.5 rounded bg-white border border-amber-300 font-mono text-[10px] text-amber-950 font-semibold"
                                >
                                  {id}
                                </span>
                              ))}
                            </div>
                          </div>
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
                    All Life Domain Cards (Click Any Heading to View Details)
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {(predictionReport?.sections || []).map((sec) => {
                      const isSelected =
                        sec.topic.toLowerCase() === selectedTopic.toLowerCase() ||
                        sec.title.toLowerCase().includes(selectedTopic.toLowerCase());

                      return (
                        <div
                          key={sec.topic}
                          onClick={() => handleSelectTopic(sec.topic)}
                          className={`p-3 rounded-xl border cursor-pointer transition-all flex flex-col justify-between ${
                            isSelected
                              ? "bg-amber-50/60 border-[#800020] shadow-xs ring-1 ring-[#800020]"
                              : "bg-white hover:border-amber-300 border-slate-200"
                          }`}
                        >
                          <div>
                            <div className="flex items-center justify-between mb-1.5">
                              <h4 className="font-serif font-bold text-xs text-[#800020] hover:underline">
                                {sec.title}
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
                              {sec.overview || sec.summary}
                            </p>
                          </div>

                          <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-[#800020] font-semibold">
                            <span>{isSelected ? "Active View" : "Click to view details"}</span>
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
                      <i className="fa-solid fa-scroll"></i> Executive Natal Overview
                    </span>
                    {predictionReport?.chart_overview && (
                      <span className="text-[11px] font-semibold text-slate-600">
                        {predictionReport.chart_overview.lagna_sign_name} Lagna &bull;{" "}
                        {predictionReport.chart_overview.rashi_sign_name} Moon
                      </span>
                    )}
                  </div>
                  <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-sans">
                    {predictionReport?.executive_overview ||
                      "Your natal chart reveals purposeful planetary vigor across pivotal angular and trinal houses. Parashari principles indicate steady progressive cultivation when natural talents are paired with structured discipline and conscious dharma."}
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
                        <span className="font-bold text-amber-950">Active Planetary Cycles: </span>
                        <span className="text-slate-700">
                          <strong>Mahadasha:</strong> {currentDasha.md.lord} (until {currentDasha.md.end}) &bull;{" "}
                          <strong>Antardasha:</strong> {currentDasha.ad?.lord || "Active"}
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
                    Core Insights &amp; Life Areas (Click Any Heading to Open)
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {(predictionReport?.sections || []).map((sec) => (
                      <div
                        key={sec.topic}
                        onClick={() => handleSelectTopic(sec.topic)}
                        className="p-3 rounded-lg bg-white border border-slate-200 hover:border-amber-400 cursor-pointer transition-colors shadow-2xs flex flex-col justify-between"
                      >
                        <div>
                          <div className="flex items-center justify-between mb-1">
                            <h4 className="font-serif font-bold text-xs text-[#800020] hover:underline">
                              {sec.title}
                            </h4>
                            <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-slate-100 text-slate-700">
                              {sec.evidence_level}
                            </span>
                          </div>
                          <p className="text-xs text-slate-600 line-clamp-2 leading-snug">
                            {sec.overview || sec.summary}
                          </p>
                        </div>
                        <div className="mt-2 pt-2 border-t border-slate-100 text-[11px] text-amber-800 font-semibold flex items-center justify-between">
                          <span>View Full Details</span>
                          <span>&rarr;</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* ── TAB: CURRENT PERIOD ── */}
            {activeTab === "current_period" && (
              <div className="space-y-4 animate-fade-in">
                <div className="p-4 rounded-xl bg-gradient-to-br from-amber-50 to-orange-50/40 border border-amber-200">
                  <h3 className="font-serif font-bold text-base text-amber-950 mb-1 flex items-center gap-2">
                    <span>⏳</span> Active Vimshottari Dasha Periods
                  </h3>
                  <p className="text-xs text-slate-600 mb-3">
                    Planetary timing modulates natal potential into concrete life experiences across specific cycles.
                  </p>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {currentDasha?.md && (
                      <div className="p-3 rounded-lg bg-white border border-amber-200 shadow-2xs">
                        <span className="text-[10px] font-bold uppercase text-amber-800 tracking-wider block">
                          Major Life Period (Mahadasha)
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
                          Sub-Period (Antardasha)
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
                    {showPratyantardasha ? "Hide Pratyantardasha" : "Show Sub-Periods (Pratyantardasha)"}
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
                <h3 className="font-serif font-bold text-base text-slate-900">AI Engine Settings</h3>
              </div>
              <button
                onClick={() => setAiSettingsOpen(false)}
                className="w-7 h-7 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-500 font-bold flex items-center justify-center text-xs"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Provider</label>
                <select
                  value={selectedProvider}
                  onChange={(e) => setSelectedProvider(e.target.value)}
                  className="w-full py-1.5 px-3 border border-slate-200 rounded-lg text-xs"
                >
                  <option value="groq">Groq Cloud (Fast &amp; Free)</option>
                  <option value="gemini">Google Gemini (Free Tier)</option>
                  <option value="openrouter">OpenRouter</option>
                  <option value="custom">Custom Endpoint</option>
                </select>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Model Selection</label>
                <input
                  type="text"
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  placeholder="e.g. llama-3.3-70b-versatile"
                  className="w-full py-1.5 px-3 border border-slate-200 rounded-lg text-xs font-mono"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">API Key (Optional override)</label>
                <input
                  type="password"
                  value={apiKeyInput}
                  onChange={(e) => setApiKeyInput(e.target.value)}
                  placeholder="Enter API key or leave blank to use server environment"
                  className="w-full py-1.5 px-3 border border-slate-200 rounded-lg text-xs"
                />
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
                className="px-4 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700 shadow-sm transition-colors"
              >
                Save AI Settings
              </button>
            </div>
          </div>
        </div>
      )}

      {/* About Modal */}
      <AboutModal isOpen={isAboutOpen} onClose={() => setIsAboutOpen(false)} />
    </div>
  );
}
