"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { LoadingSpinner } from "../../components/LoadingSpinner";
import { ReportForm } from "../../components/ReportForm";
import { useAuth } from "../../components/AuthProvider";
import AboutModal from "../../components/AboutModal";
import { PredictionPdfViewer } from "../../components/PredictionPdfViewer";
import {
  generatePredictions,
  getPredictions,
  regeneratePredictionSection,
  savePredictionSection,
  renderPredictionPdf,
  calculateReport,
  getAiConfig,
  updateAiConfig,
  API,
} from "../../services/api";
import type { ReportInput } from "../../types/report";
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
  language: "en",
  planet_overrides: {},
  override_moon_longitude: "",
  override_ascendant_longitude: "",
};

export default function PredictionsPage() {
  const router = useRouter();
  const { user, isAdmin, logout } = useAuth();

  // Core Prediction & Form States
  const [formValue, setFormValue] = useState<ReportInput>(initialFormValue);
  const [showBirthForm, setShowBirthForm] = useState(false);
  const [predictionReport, setPredictionReport] = useState<PredictionReport | null>(null);

  // UI Tabs & Navigation States
  const [activeTab, setActiveTab] = useState<"overview" | "life_areas" | "current_period" | "advanced">("overview");
  const [selectedTopic, setSelectedTopic] = useState<string>("career");
  const [expandedWhyThis, setExpandedWhyThis] = useState<Record<string, boolean>>({});
  const [showPratyantardasha, setShowPratyantardasha] = useState<boolean>(false);

  // Manual Editing Drawer (inside Advanced)
  const [isEditDrawerOpen, setIsEditDrawerOpen] = useState(false);
  const [editingTopic, setEditingTopic] = useState<string>("career");
  const [editContent, setEditContent] = useState<string>("");
  const [savingSection, setSavingSection] = useState(false);

  // PDF & Settings
  const [includeAppendix, setIncludeAppendix] = useState<boolean>(false);
  const [compiledPdfUrl, setCompiledPdfUrl] = useState<string>("");
  const [previewUrl, setPreviewUrl] = useState<string>("");
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

  // Modals & Navigation
  const [isAboutOpen, setIsAboutOpen] = useState(false);

  // ── Load Initial Data ──
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
          handleGenerateAll(parsed, false);
        } catch (e) {
          console.error("Error reading stored prediction details:", e);
        }
      } else {
        setShowBirthForm(true);
      }
    }
  }, []);

  // ── Render Preview & PDF ──
  const refreshPreview = useCallback(
    async (report: PredictionReport) => {
      try {
        const payloadWithOption = {
          ...report,
          include_technical_appendix: includeAppendix,
        };
        const res = await renderPredictionPdf(payloadWithOption);
        const fullPdfPath = `${API}${res.pdf_url}`;
        setCompiledPdfUrl(fullPdfPath);

        const blob = new Blob([res.html], { type: "text/html" });
        const bUrl = URL.createObjectURL(blob);
        setPreviewUrl(bUrl);
      } catch (err: any) {
        console.error("Failed to render prediction preview:", err);
      }
    },
    [includeAppendix]
  );

  useEffect(() => {
    if (predictionReport) {
      refreshPreview(predictionReport);
    }
  }, [predictionReport, refreshPreview]);

  // ── Generate All Predictions ──
  async function handleGenerateAll(overrideInput?: ReportInput, force: boolean = false) {
    const input = overrideInput || formValue;
    if (!input.name || !input.dob || !input.time || !input.place) {
      setError("Please fill in client Name, Date of Birth, Time, and Birth Place.");
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
        include_technical_appendix: includeAppendix,
      });

      setPredictionReport(report);
      setShowBirthForm(false);
      setSuccessMessage("Predictions generated successfully with Jyotish Rulebook v2.0!");
      setTimeout(() => setSuccessMessage(""), 5000);
    } catch (err: any) {
      console.error("Prediction generation error:", err);
      setError(err.message || "Failed to generate predictions.");
    } finally {
      setLoading(false);
    }
  }

  // ── Save Manual Section Edit ──
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

  // ── Save AI Settings ──
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

  const activeSection = useMemo(() => {
    if (!predictionReport || !predictionReport.sections) return null;
    return predictionReport.sections.find((s) => s.topic === selectedTopic) || predictionReport.sections[0] || null;
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
    <div className="min-h-screen bg-[#fcfbf7] flex flex-col font-sans text-slate-800">
      {/* ── Top Header Navigation ── */}
      <header className="bg-white/95 backdrop-blur-md border-b border-[#ebdcb9] sticky top-0 z-30 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push("/create-report")}
              className="w-8 h-8 rounded-full bg-amber-50 hover:bg-amber-100 flex items-center justify-center text-amber-900 transition-colors"
              title="Return to Chart Sheet"
            >
              <i className="fa-solid fa-arrow-left text-sm"></i>
            </button>
            <div className="flex items-center gap-2">
              <span className="w-8 h-8 rounded-lg bg-[#800020] text-amber-300 flex items-center justify-center font-bold text-base shadow-xs">
                🕉️
              </span>
              <div>
                <h1 className="font-serif font-bold text-base sm:text-lg text-[#800020] leading-none">
                  Predictions Workspace
                </h1>
                <p className="text-[0.6875rem] text-amber-900 font-medium tracking-wide">
                  Complete Jyotish Prediction Engine &amp; AI Validation
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            <button
              onClick={() => router.push("/create-report")}
              className="px-3 py-1.5 rounded-lg border border-[#ebdcb9] hover:bg-amber-50/70 text-amber-900 text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <i className="fa-solid fa-chart-pie text-xs"></i> Chart Sheet
            </button>

            <button
              onClick={() => setAiSettingsOpen(true)}
              className="px-3 py-1.5 rounded-lg bg-indigo-50 border border-indigo-200 hover:bg-indigo-100 text-indigo-900 text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <i className="fa-solid fa-microchip text-xs"></i> AI Engine Settings
            </button>

            <button
              onClick={() => setIsAboutOpen(true)}
              className="px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-medium hidden sm:flex items-center gap-1"
            >
              <i className="fa-solid fa-circle-info text-xs"></i> About
            </button>

            {isAdmin && (
              <Link
                href="/admin"
                className="px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-medium flex items-center gap-1"
              >
                <i className="fa-solid fa-shield text-xs"></i> Admin
              </Link>
            )}

            <button
              onClick={logout}
              className="px-3 py-1.5 rounded-lg border border-red-200 text-red-700 hover:bg-red-50 text-xs font-medium flex items-center gap-1 transition-colors"
            >
              <i className="fa-solid fa-arrow-right-from-bracket text-xs"></i> Logout
            </button>
          </div>
        </div>
      </header>

      {/* ── Status Messages ── */}
      {error && (
        <div className="max-w-7xl mx-auto w-full px-4 mt-3">
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-800 text-xs flex items-center justify-between">
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
        <div className="max-w-7xl mx-auto w-full px-4 mt-3">
          <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3 text-emerald-800 text-xs flex items-center justify-between">
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

      {/* ── Main Two-Column Layout ── */}
      <main className="max-w-7xl mx-auto w-full p-4 flex-1 grid grid-cols-12 gap-5">
        {/* ════════════ LEFT COLUMN: PDF VIEWER & TOOLBAR (5 Cols) ════════════ */}
        <section className="col-span-12 lg:col-span-5 flex flex-col gap-3">
          {/* Compact Top Toolbar */}
          <div className="bg-white border border-[#ebdcb9] rounded-xl p-3 shadow-xs flex flex-col gap-2.5">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
              <span className="flex items-center gap-1.5 text-amber-950 font-serif">
                <i className="fa-solid fa-sliders text-[#800020]"></i> Prediction Controls
              </span>
              <button
                onClick={() => setShowBirthForm(!showBirthForm)}
                className="text-[11px] text-amber-800 hover:underline flex items-center gap-1 font-sans"
              >
                <i className="fa-solid fa-id-card"></i> {showBirthForm ? "Hide Details" : "Edit Client"}
              </button>
            </div>

            {/* Birth Details Drawer/Collapse */}
            {showBirthForm && (
              <div className="pt-2 border-t border-slate-100 animate-fade-in">
                <ReportForm
                  value={formValue}
                  onChange={setFormValue}
                  onSubmit={() => handleGenerateAll(formValue, true)}
                  loading={loading}
                />
              </div>
            )}

            {/* Compact Toolbar Row */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <label className="text-[10px] uppercase font-bold text-slate-400 block mb-0.5">AI Provider</label>
                <select
                  value={selectedProvider}
                  onChange={(e) => setSelectedProvider(e.target.value)}
                  className="w-full text-xs py-1 px-2 border border-slate-200 rounded-md bg-slate-50 focus:bg-white"
                >
                  <option value="groq">Groq (Ultra-Fast Free)</option>
                  <option value="gemini">Google Gemini</option>
                  <option value="openrouter">OpenRouter</option>
                  <option value="custom">Custom Endpoint</option>
                </select>
              </div>

              <div>
                <label className="text-[10px] uppercase font-bold text-slate-400 block mb-0.5">Model</label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full text-xs py-1 px-2 border border-slate-200 rounded-md bg-slate-50 focus:bg-white"
                >
                  <option value="llama-3.3-70b-versatile">LLaMA 3.3 70B</option>
                  <option value="llama-3.1-8b-instant">LLaMA 3.1 8B</option>
                  <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
                  <option value="gemini-2.0-flash">Gemini 2.0 Flash</option>
                </select>
              </div>
            </div>

            {/* Checkbox and Regenerate Button */}
            <div className="flex items-center justify-between pt-1 text-xs">
              <label className="flex items-center gap-2 cursor-pointer select-none text-slate-700">
                <input
                  type="checkbox"
                  checked={includeAppendix}
                  onChange={(e) => setIncludeAppendix(e.target.checked)}
                  className="rounded text-[#800020] focus:ring-[#800020]"
                />
                <span className="text-[11px] font-medium">Include technical appendix</span>
              </label>

              <button
                onClick={() => handleGenerateAll(formValue, true)}
                disabled={loading}
                className="px-3 py-1.5 rounded-lg bg-[#800020] hover:bg-[#600018] text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-xs disabled:opacity-50"
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

          {/* Left Panel PDF Viewer */}
          <div className="flex-1 min-h-[580px] bg-white border border-[#ebdcb9] rounded-xl overflow-hidden shadow-xs flex flex-col">
            {loading ? (
              <div className="flex-1 flex flex-col items-center justify-center p-8 text-slate-500 gap-3">
                <LoadingSpinner />
                <span className="text-xs font-medium">Computing planetary rules &amp; compiling PDF...</span>
              </div>
            ) : compiledPdfUrl ? (
              <PredictionPdfViewer
                pdfUrl={compiledPdfUrl}
                downloadFilename={`${formValue.name || "Client"}_Jyotish_Predictions.pdf`}
                onReload={() => handleGenerateAll(formValue, true)}
              />
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-slate-400 gap-3">
                <div className="w-14 h-14 rounded-full bg-amber-50 text-amber-800 flex items-center justify-center text-2xl">
                  🕉️
                </div>
                <h3 className="font-serif font-bold text-slate-700 text-sm">Ready to Generate Predictions</h3>
                <p className="text-xs text-slate-500 max-w-xs">
                  Fill in client birth data or click generate to run the verified Parashari Rulebook v2.0 engine.
                </p>
                <button
                  onClick={() => handleGenerateAll(formValue, true)}
                  className="mt-2 px-4 py-2 bg-[#800020] text-white rounded-lg text-xs font-semibold shadow-sm hover:bg-[#600018] transition-colors"
                >
                  Generate Predictions
                </button>
              </div>
            )}
          </div>
        </section>

        {/* ════════════ RIGHT COLUMN: 4 TABS INTERACTIVE WORKSPACE (7 Cols) ════════════ */}
        <section className="col-span-12 lg:col-span-7 flex flex-col gap-3">
          <div className="bg-white border border-[#ebdcb9] rounded-xl shadow-xs overflow-hidden flex flex-col min-h-[660px]">
            {/* Top Tab Bar */}
            <div className="flex items-center justify-between border-b border-[#ebdcb9] bg-[#fffdfa] px-4 pt-2">
              <div className="flex items-center gap-1 sm:gap-2">
                {[
                  { id: "overview", label: "Overview", icon: "fa-compass" },
                  { id: "life_areas", label: "Life Areas", icon: "fa-layer-group" },
                  { id: "current_period", label: "Current Period", icon: "fa-clock" },
                  { id: "advanced", label: "Advanced", icon: "fa-code-branch" },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`px-3 py-2 text-xs font-semibold border-b-2 flex items-center gap-1.5 transition-colors ${
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
                <span className="text-[11px] font-mono text-amber-900 hidden sm:inline-block">
                  v{predictionReport.ruleset.version} Parashari
                </span>
              )}
            </div>

            {/* Tab Body */}
            <div className="p-4 sm:p-5 flex-1 overflow-y-auto">
              {/* ── TAB 1: OVERVIEW ── */}
              {activeTab === "overview" && (
                <div className="space-y-4 animate-fade-in">
                  {/* Executive Overview Synthesis (<= 120 words) */}
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

                  {/* Insight Chips (<= 5 chips, each 2 lines + "Why this?") */}
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2.5">
                      Key Life Insights &amp; Focus Trends
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {(predictionReport?.sections || []).slice(0, 4).map((sec, i) => {
                        const chipKey = `chip-${sec.topic}`;
                        const isExpanded = !!expandedWhyThis[chipKey];
                        const firstTheme = sec.themes?.[0] || sec.summary;

                        return (
                          <div
                            key={sec.topic}
                            className="p-3 rounded-lg bg-white border border-slate-200 hover:border-amber-300 transition-colors shadow-2xs flex flex-col justify-between"
                          >
                            <div>
                              <div className="flex items-center justify-between mb-1">
                                <span className="font-serif font-bold text-xs text-[#800020]">{sec.title}</span>
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
                              <p className="text-xs text-slate-600 line-clamp-2 leading-snug">{firstTheme}</p>
                            </div>

                            <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
                              <button
                                onClick={() => toggleWhyThis(chipKey)}
                                className="text-amber-800 hover:text-amber-950 font-semibold flex items-center gap-1"
                              >
                                <i className="fa-solid fa-circle-question text-[10px]"></i>
                                Why this?
                              </button>
                              <button
                                onClick={() => {
                                  setSelectedTopic(sec.topic);
                                  setActiveTab("life_areas");
                                }}
                                className="text-slate-500 hover:text-slate-800"
                              >
                                View Domain &rarr;
                              </button>
                            </div>

                            {/* Collapsible Why This justification */}
                            {isExpanded && (
                              <div className="mt-2 p-2 bg-amber-50/70 rounded text-[11px] text-amber-950 border border-amber-200">
                                <div className="font-bold mb-0.5">Evidence Grounding:</div>
                                <div>Level: {sec.evidence_level} ({sec.lean})</div>
                                <div className="text-[10px] text-slate-600 mt-1">
                                  Rule IDs: {(sec.basis_ids || sec.rule_ids || []).slice(0, 3).join(", ") || "Parashari Core"}
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}

              {/* ── TAB 2: LIFE AREAS (8 CARDS) ── */}
              {activeTab === "life_areas" && (
                <div className="space-y-4 animate-fade-in">
                  {/* 8 Cards Selector */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {(predictionReport?.sections || []).slice(0, 8).map((sec) => (
                      <button
                        key={sec.topic}
                        onClick={() => setSelectedTopic(sec.topic)}
                        className={`p-2.5 rounded-lg border text-left transition-all ${
                          selectedTopic === sec.topic
                            ? "bg-[#800020] text-white border-[#800020] shadow-xs"
                            : "bg-white hover:bg-amber-50/50 border-slate-200 text-slate-700"
                        }`}
                      >
                        <div className="font-serif font-bold text-xs truncate">{sec.title}</div>
                        <div
                          className={`text-[9px] uppercase tracking-wider font-semibold ${
                            selectedTopic === sec.topic ? "text-amber-200" : "text-slate-400"
                          }`}
                        >
                          {sec.evidence_level}
                        </div>
                      </button>
                    ))}
                  </div>

                  {/* Active Life Area View */}
                  {activeSection && (
                    <div className="p-4 sm:p-5 rounded-xl bg-white border border-[#ebdcb9] shadow-xs space-y-4">
                      {/* Section Header */}
                      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                        <div>
                          <h2 className="font-serif font-bold text-base sm:text-lg text-[#800020]">
                            {activeSection.title}
                          </h2>
                          <span className="text-[11px] text-slate-500 font-medium">
                            Natal Planetary Analysis &bull; Whole Sign Parashari
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

                      {/* Overview (40-70 words) */}
                      <div>
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">Domain Overview</h4>
                        <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-sans">
                          {activeSection.overview || activeSection.summary}
                        </p>
                      </div>

                      {/* Key Themes (3 items, <= 18 words each) */}
                      {activeSection.themes && activeSection.themes.length > 0 && (
                        <div>
                          <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-800 mb-1.5 flex items-center gap-1.5">
                            <i className="fa-solid fa-sparkles text-emerald-600"></i> Core Themes
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

                      {/* Growth Challenges (2 items) */}
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
                      <div className="pt-3 border-t border-slate-100">
                        <button
                          onClick={() => toggleWhyThis(`topic-${activeSection.topic}`)}
                          className="w-full flex items-center justify-between text-xs font-semibold text-slate-700 p-2 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors"
                        >
                          <span className="flex items-center gap-1.5">
                            <i className="fa-solid fa-circle-info text-amber-800"></i>
                            Why this? (Classical Evidence &amp; Rule Basis)
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
                                Verified Basis IDs:
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
                  )}
                </div>
              )}

              {/* ── TAB 3: CURRENT PERIOD ── */}
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

                  {/* 3 Active Period Themes */}
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

                    {/* Next AD Change */}
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

                  {/* Pratyantardasha Toggle (Hidden by Default) */}
                  <div className="pt-2">
                    <button
                      onClick={() => setShowPratyantardasha(!showPratyantardasha)}
                      className="text-xs font-semibold text-slate-600 hover:text-slate-900 flex items-center gap-1.5"
                    >
                      <i className={`fa-solid ${showPratyantardasha ? "fa-eye-slash" : "fa-eye"}`}></i>
                      {showPratyantardasha ? "Hide Pratyantardasha Periods" : "Show Sub-Periods (Pratyantardasha)"}
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

              {/* ── TAB 4: ADVANCED ── */}
              {activeTab === "advanced" && (
                <div className="space-y-4 animate-fade-in">
                  {/* Top Action to Open Edit Drawer */}
                  <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200">
                    <div>
                      <h4 className="font-bold text-xs text-slate-800">Astrologer Manual Review &amp; Edits</h4>
                      <p className="text-[11px] text-slate-500">
                        Customize or refine individual prediction sections without modifying underlying calculations.
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
                          className="p-2.5 rounded bg-slate-50 border border-slate-200 flex items-center justify-between text-xs"
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
          </div>
        </section>
      </main>

      {/* ── Edit Section Drawer / Modal (Inside Advanced) ── */}
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
