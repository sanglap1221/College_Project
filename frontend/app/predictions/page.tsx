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
  getPredictions,
  regeneratePredictionSection,
  savePredictionSection,
  renderPredictionPdf,
  renderPdf,
  calculateReport,
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
  const [activeSectionTopic, setActiveSectionTopic] = useState<string>("personality");
  const [editedSections, setEditedSections] = useState<Record<string, string>>({});
  const [editorMode, setEditorMode] = useState<"read" | "edit">("read");

  // UI & Loading States
  const [loading, setLoading] = useState(false);
  const [sectionRegenerating, setSectionRegenerating] = useState<string | null>(null);
  const [savingSection, setSavingSection] = useState<string | null>(null);
  const [previewHtml, setPreviewHtml] = useState<string>("");
  const [previewUrl, setPreviewUrl] = useState<string>("");
  const [chartPdfUrl, setChartPdfUrl] = useState<string>("");
  const [compiledPdfUrl, setCompiledPdfUrl] = useState<string>("");
  const [activePdfTab, setActivePdfTab] = useState<"prediction" | "chart">("prediction");
  const [error, setError] = useState<string>("");
  const [successMessage, setSuccessMessage] = useState<string>("");

  // AI Review & Configuration States
  const [useAi, setUseAi] = useState<boolean>(true);
  const [aiConfig, setAiConfig] = useState<AiConfigResponse | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<string>("groq");
  const [selectedModel, setSelectedModel] = useState<string>("llama-3.3-70b-versatile");
  const [aiSettingsOpen, setAiSettingsOpen] = useState(false);
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [viewingOriginalDraft, setViewingOriginalDraft] = useState<Record<string, boolean>>({});

  // Modals & Navigation States
  const [isAboutOpen, setIsAboutOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // ── Load Initial Data (Session Storage or History) ──
  useEffect(() => {
    if (typeof window !== "undefined") {
      // 1. Fetch AI config status safely
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

      // 2. Check for chart PDF from create-report
      const storedChartPdf = sessionStorage.getItem("pending_chart_pdf_url");
      if (storedChartPdf) {
        setChartPdfUrl(storedChartPdf);
      }

      // 3. Check for passed birth details or existing prediction
      const passedPred = sessionStorage.getItem("pending_prediction_details");
      const passedBirth = sessionStorage.getItem("pending_birth_details");
      const activeData = passedPred || passedBirth;

      if (activeData) {
        try {
          const parsed = JSON.parse(activeData) as ReportInput;
          setFormValue(parsed);
          handleGenerateAll(parsed);
        } catch (e) {
          console.error("Error reading stored prediction details:", e);
        }
      } else {
        setShowBirthForm(true);
      }
    }
  }, []);

  // ── Render Preview HTML whenever prediction report updates ──
  const refreshPreview = useCallback(async (report: PredictionReport) => {
    try {
      const res = await renderPredictionPdf(report);
      setPreviewHtml(res.html);
      setCompiledPdfUrl(res.pdf_url);

      const blob = new Blob([res.html], { type: "text/html" });
      const bUrl = URL.createObjectURL(blob);
      setPreviewUrl(bUrl);
    } catch (err: any) {
      console.error("Failed to render prediction preview:", err);
    }
  }, []);

  useEffect(() => {
    if (predictionReport) {
      refreshPreview(predictionReport);
    }
  }, [predictionReport, refreshPreview]);

  // ── Generate All Predictions ──
  async function handleGenerateAll(overrideInput?: ReportInput) {
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
      });

      setPredictionReport(report);
      setShowBirthForm(false);
      setEditedSections({});
      setSuccessMessage("Predictions generated successfully using Jyotish Rulebook v2.0!");
      setTimeout(() => setSuccessMessage(""), 5000);

      // If chart PDF wasn't loaded from create-report, generate it in background
      if (!chartPdfUrl) {
        calculateReport(input)
          .then((calc) => renderPdf(calc))
          .then((pdfRes) => setChartPdfUrl(pdfRes.preview_url))
          .catch((e) => console.warn("Could not generate chart PDF preview:", e));
      }
    } catch (err: any) {
      console.error("Prediction generation error:", err);
      setError(err.message || "Failed to generate predictions.");
    } finally {
      setLoading(false);
    }
  }

  // ── Regenerate Single Section ──
  async function handleRegenerateSection(topic: string) {
    if (!predictionReport) return;
    setSectionRegenerating(topic);
    setError("");

    try {
      const updated = await regeneratePredictionSection(
        predictionReport.report_id,
        topic,
        useAi,
        selectedProvider,
        selectedModel,
        formValue
      );
      setPredictionReport(updated);
      setEditedSections((prev) => {
        const next = { ...prev };
        delete next[topic];
        return next;
      });
      setSuccessMessage(`Section '${topic}' regenerated successfully!`);
      setTimeout(() => setSuccessMessage(""), 4000);
    } catch (err: any) {
      setError(err.message || `Failed to regenerate section '${topic}'`);
    } finally {
      setSectionRegenerating(null);
    }
  }

  // ── Save Manual Edits ──
  async function handleSaveSectionEdit(topic: string) {
    if (!predictionReport) return;
    const content = editedSections[topic];
    if (content === undefined) return;

    setSavingSection(topic);
    try {
      await savePredictionSection(predictionReport.report_id, topic, content);

      setPredictionReport((prev) => {
        if (!prev) return prev;
        const nextSections = prev.sections.map((s) =>
          s.topic === topic ? { ...s, prediction: content, status: "manual_edited" } : s
        );
        return { ...prev, sections: nextSections };
      });

      setSuccessMessage("Manual edits saved and report preview updated.");
      setTimeout(() => setSuccessMessage(""), 4000);
    } catch (err: any) {
      setError(err.message || "Failed to save section edits.");
    } finally {
      setSavingSection(null);
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
      const refreshed = await getAiConfig();
      if (refreshed) setAiConfig(refreshed);
      setAiSettingsOpen(false);
      setApiKeyInput("");
      setSuccessMessage("AI configuration updated successfully!");
      setTimeout(() => setSuccessMessage(""), 4000);
    } catch (err: any) {
      setError(err.message || "Failed to update AI configuration.");
    }
  }

  // Active section helper
  const activeSection = useMemo(() => {
    if (!predictionReport || !predictionReport.sections) return null;
    return predictionReport.sections.find((s) => s.topic === activeSectionTopic) || predictionReport.sections[0];
  }, [predictionReport, activeSectionTopic]);

  return (
    <div className="min-h-screen flex flex-col" style={{ fontFamily: "'Inter', 'Hind Siliguri', sans-serif", background: "#f7f5f0", color: "#334155" }}>

      {/* ── Background Decorative Gradient Blurs ── */}
      <div className="absolute top-0 left-0 w-[30vw] h-[30vw] min-w-[15rem] min-h-[15rem] bg-amber-100 opacity-20 rounded-full blur-3xl pointer-events-none -translate-x-1/2 -translate-y-1/2" />
      <div className="absolute bottom-0 right-0 w-[30vw] h-[30vw] min-w-[15rem] min-h-[15rem] bg-red-100 opacity-20 rounded-full blur-3xl pointer-events-none translate-x-1/2 translate-y-1/2" />

      {/* ── Fixed Header ── */}
      <header className="fixed top-0 left-0 right-0 no-print w-full py-3 px-3 sm:px-6 border-b flex items-center justify-between shadow-sm z-30 h-[65px]" style={{ borderColor: "#ebdcb9", background: "#fdfcf7" }}>
        <div className="flex items-center gap-2 sm:gap-3">
          <button
            onClick={() => router.push("/create-report")}
            className="flex items-center justify-center w-8 h-8 rounded-lg hover:bg-amber-100/80 transition-colors border shadow-sm"
            style={{ color: "#92400e", borderColor: "rgba(245, 158, 11, 0.25)", background: "#fffbeb" }}
            title="Return to Visual Chart Board"
          >
            <i className="fa-solid fa-arrow-left text-xs" />
          </button>
          <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg flex items-center justify-center text-white font-bold text-base sm:text-lg shadow-md" style={{ background: "#800020" }}>
            🕉️
          </div>
          <div>
            <h1 className="text-sm sm:text-lg font-bold tracking-tight" style={{ color: "#1a365d" }}>
              Predictions Workspace
            </h1>
            <p className="hidden sm:block text-xs font-medium" style={{ color: "rgba(146, 64, 14, 0.8)" }}>
              Complete Jyotish Prediction Engine &amp; AI Review
            </p>
          </div>
        </div>

        {/* Header Right Actions */}
        <div className="flex items-center gap-2 sm:gap-3">
          <Link
            href="/create-report"
            className="hidden md:flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg transition-all border shadow-sm"
            style={{ color: "#92400e", background: "#fffbeb", borderColor: "#fde68a" }}
            title="Switch to Chart View"
          >
            <i className="fa-solid fa-chart-pie"></i> Chart Sheet
          </Link>

          <button
            type="button"
            onClick={() => setAiSettingsOpen(true)}
            className="hidden md:flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg transition-all border shadow-sm"
            style={{ color: "#4f46e5", background: "#eef2ff", borderColor: "#c7d2fe" }}
            title="AI Model & API Key Settings"
          >
            <i className="fa-solid fa-brain"></i> AI Engine Settings
          </button>

          <button
            type="button"
            onClick={() => setIsAboutOpen(true)}
            className="hidden md:flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg transition-all border shadow-sm"
            style={{ color: "#b45309", background: "#fffbeb", borderColor: "#fde68a" }}
          >
            <i className="fa-solid fa-circle-info"></i> About
          </button>

          {isAdmin && (
            <Link
              href="/admin"
              className="hidden md:flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg transition-all border shadow-sm"
              style={{ color: "#92400e", background: "#fffbeb", borderColor: "#f59e0b40" }}
            >
              <i className="fa-solid fa-shield-halved"></i> Admin
            </Link>
          )}

          <button
            type="button"
            onClick={logout}
            className="hidden md:flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg transition-all border shadow-sm"
            style={{ color: "#ef4444", background: "#fef2f2", borderColor: "#fecaca" }}
          >
            <i className="fa-solid fa-right-from-bracket"></i> Logout
          </button>

          {/* Mobile hamburger menu toggle */}
          <button
            type="button"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden flex items-center justify-center w-8 h-8 rounded-lg border text-slate-700 bg-white"
            style={{ borderColor: "#ebdcb9" }}
          >
            <i className={`fa-solid ${isMobileMenuOpen ? "fa-xmark" : "fa-bars"}`}></i>
          </button>
        </div>
      </header>

      {/* Spacer for fixed header */}
      <div className="h-[65px] shrink-0 no-print" />

      {/* ── Status Banners (Error / Success) ── */}
      {error && (
        <div className="mx-4 mt-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 shadow-sm flex items-center justify-between z-20">
          <div className="flex items-center gap-2">
            <i className="fa-solid fa-triangle-exclamation text-red-500"></i>
            <span className="font-bold">Error:</span> {error}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleGenerateAll()}
              className="px-2.5 py-1 text-xs font-bold rounded bg-red-600 text-white hover:bg-red-700 transition"
            >
              Retry
            </button>
            <button onClick={() => setError("")} className="text-red-500 hover:text-red-700">
              <i className="fa-solid fa-xmark"></i>
            </button>
          </div>
        </div>
      )}

      {successMessage && (
        <div className="mx-4 mt-4 rounded-xl border border-green-200 bg-green-50 p-3 text-sm text-green-800 shadow-sm flex items-center gap-2 z-20">
          <i className="fa-solid fa-circle-check text-green-600"></i>
          <span>{successMessage}</span>
        </div>
      )}

      {/* ── Outdated Chart Warning Banner ── */}
      {predictionReport?.is_outdated && (
        <div className="mx-4 mt-4 rounded-xl border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900 shadow-sm flex items-center justify-between z-20">
          <div className="flex items-center gap-2">
            <i className="fa-solid fa-triangle-exclamation text-amber-600"></i>
            <span><strong>Chart Updated:</strong> The underlying birth chart facts have changed since this prediction report was generated.</span>
          </div>
          <button
            onClick={() => handleGenerateAll()}
            className="px-3 py-1 bg-amber-600 text-white rounded-lg text-xs font-semibold hover:bg-amber-700 transition"
          >
            Regenerate Now
          </button>
        </div>
      )}

      {/* ── MAIN WORKSPACE (Left: Prediction Descriptions & Editor, Right: Live PDF Preview) ── */}
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-12 items-stretch overflow-y-auto lg:overflow-hidden h-auto lg:h-[calc(100vh-65px)]">

        {/* ── LEFT COLUMN: Prediction Descriptions & Section Controls (lg:col-span-5) ── */}
        <section className="lg:col-span-5 flex flex-col overflow-y-auto border-r border-[#ebdcb9] bg-white">

          {/* Left Panel Header with Mode Toggle */}
          <div className="p-3.5 flex items-center justify-between no-print border-b" style={{ background: "rgba(255, 251, 235, 0.7)", borderColor: "#ebdcb9" }}>
            <div className="flex items-center gap-2">
              <span className="text-xs px-2.5 py-1 rounded-md font-bold uppercase tracking-wider" style={{ background: "rgba(128, 0, 32, 0.1)", color: "#800020" }}>
                Prediction Descriptions
              </span>
              <span className="text-[0.6875rem] font-semibold text-slate-500">
                Rulebook v2.0
              </span>
            </div>

            <div className="flex items-center gap-1.5">
              {predictionReport && (
                <div className="flex bg-slate-100 p-0.5 rounded-lg border border-slate-200">
                  <button
                    type="button"
                    onClick={() => setEditorMode("read")}
                    className={`px-2 py-0.5 text-[0.6875rem] font-bold rounded-md transition ${editorMode === "read" ? "bg-white text-[#800020] shadow-sm" : "text-slate-500"}`}
                  >
                    📖 Read
                  </button>
                  <button
                    type="button"
                    onClick={() => setEditorMode("edit")}
                    className={`px-2 py-0.5 text-[0.6875rem] font-bold rounded-md transition ${editorMode === "edit" ? "bg-white text-[#800020] shadow-sm" : "text-slate-500"}`}
                  >
                    ✍️ Edit
                  </button>
                </div>
              )}
              <button
                type="button"
                onClick={() => setShowBirthForm(!showBirthForm)}
                className="text-xs font-semibold px-2 py-1 rounded-md text-slate-600 hover:text-slate-900 hover:bg-amber-100/50"
              >
                <i className="fa-solid fa-id-card"></i> {showBirthForm ? "Hide" : "Client"}
              </button>
            </div>
          </div>

          {/* Collapsible Birth Details Form */}
          {showBirthForm && (
            <div className="p-4 border-b bg-[#fdfcf9]" style={{ borderColor: "#ebdcb9" }}>
              <div className="text-center mb-3">
                <span className="text-xs font-bold uppercase tracking-wider block" style={{ color: "#92400e" }}>
                  Client Birth Facts
                </span>
              </div>
              <ReportForm value={formValue} onChange={setFormValue} onSubmit={() => handleGenerateAll()} loading={loading} />
            </div>
          )}

          {/* Quick Engine Actions & Model Settings Bar */}
          <div className="px-4 py-2.5 border-b bg-[#fffdfa]" style={{ borderColor: "#ebdcb9" }}>
            <div className="flex items-center justify-between mb-2">
              <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useAi}
                  onChange={(e) => setUseAi(e.target.checked)}
                  className="rounded border-slate-300 text-maroon-600 focus:ring-amber-500 h-3.5 w-3.5"
                />
                <span>AI Review &amp; English Writing</span>
              </label>

              <span className="text-[0.625rem] font-bold px-2 py-0.5 rounded-full" style={{ background: aiConfig?.is_configured ? "#dcfce7" : "#fef3c7", color: aiConfig?.is_configured ? "#166534" : "#92400e" }}>
                {aiConfig?.is_configured ? `${aiConfig.active_provider.toUpperCase()} Ready` : "Rulebook Draft"}
              </span>
            </div>

            <button
              type="button"
              onClick={() => handleGenerateAll()}
              disabled={loading}
              className="w-full py-2 px-3 rounded-lg text-white font-bold text-xs shadow-sm transition-all flex items-center justify-center gap-2"
              style={{ background: "linear-gradient(135deg, #800020, #92400e)" }}
            >
              {loading ? <LoadingSpinner /> : <i className="fa-solid fa-wand-magic-sparkles"></i>}
              <span>{loading ? "Analyzing Chart & Writing Predictions..." : predictionReport ? "Regenerate All Predictions" : "Generate Predictions from Chart"}</span>
            </button>
          </div>

          {/* Section Navigation Pills / Tabs */}
          {predictionReport && predictionReport.sections && (
            <div className="px-3 py-2 border-b bg-[#fafaf8] overflow-x-auto whitespace-nowrap flex gap-1.5 no-scrollbar">
              {predictionReport.sections.map((sec) => {
                const isActive = activeSectionTopic === sec.topic;
                const isEdited = sec.status === "manual_edited" || editedSections[sec.topic] !== undefined;
                return (
                  <button
                    key={sec.topic}
                    onClick={() => setActiveSectionTopic(sec.topic)}
                    className="px-2.5 py-1 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 shrink-0"
                    style={{
                      background: isActive ? "#800020" : "#ffffff",
                      color: isActive ? "#ffffff" : "#475569",
                      border: isActive ? "1px solid #800020" : "1px solid #e2e8f0",
                      boxShadow: isActive ? "0 2px 4px rgba(128,0,32,0.15)" : "none",
                    }}
                  >
                    <span>{sec.title}</span>
                    {isEdited && (
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-400" title="Manually edited" />
                    )}
                  </button>
                );
              })}
            </div>
          )}

          {/* Active Section Description / Editor */}
          {activeSection ? (
            <div className="p-4 flex-1 flex flex-col overflow-y-auto">
              {/* Section Header & Metadata */}
              <div className="flex items-start justify-between mb-3 pb-2 border-b border-slate-100">
                <div>
                  <h3 className="font-bold text-base text-[#800020] flex items-center gap-2">
                    {activeSection.title}
                  </h3>
                  <p className="text-[0.6875rem] text-slate-500 mt-0.5">
                    {activeSection.explanation}
                  </p>
                </div>

                <div className="flex items-center gap-1.5">
                  <span
                    className="text-[0.625rem] font-bold px-2 py-0.5 rounded-full uppercase"
                    style={{
                      background: activeSection.evidence_level === "Convergent" ? "#dcfce7" : activeSection.evidence_level === "Moderate" ? "#fef3c7" : "#f1f5f9",
                      color: activeSection.evidence_level === "Convergent" ? "#166534" : activeSection.evidence_level === "Moderate" ? "#92400e" : "#475569",
                    }}
                  >
                    {activeSection.evidence_level} ({activeSection.lean})
                  </span>
                  <span className="text-[0.625rem] font-semibold px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                    {activeSection.status}
                  </span>
                </div>
              </div>

              {/* Supporting / Modifying Facts Box */}
              <div className="mb-3 p-2.5 rounded-lg border border-amber-200 bg-amber-50/50 text-xs">
                <div className="font-bold text-[#92400e] text-[0.6875rem] uppercase mb-1">
                  Astrological Grounding Facts
                </div>
                {activeSection.supporting_factors && activeSection.supporting_factors.length > 0 && (
                  <div className="text-[0.6875rem] text-slate-700 mb-1">
                    <strong className="text-green-700">Supporting:</strong>{" "}
                    {activeSection.supporting_factors.map((f, idx) => (
                      <span key={idx} className="mr-1.5 inline-block">
                        • {f.interpretation} <code className="text-[0.625rem] bg-white px-1 rounded border">{f.rule_id}</code>
                      </span>
                    ))}
                  </div>
                )}
                {activeSection.challenging_factors && activeSection.challenging_factors.length > 0 && (
                  <div className="text-[0.6875rem] text-slate-700">
                    <strong className="text-amber-800">Modifying:</strong>{" "}
                    {activeSection.challenging_factors.map((f, idx) => (
                      <span key={idx} className="mr-1.5 inline-block">
                        • {f.interpretation} <code className="text-[0.625rem] bg-white px-1 rounded border">{f.rule_id}</code>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* READ MODE: Rich Styled Prediction Narrative */}
              {editorMode === "read" ? (
                <div className="flex-1 overflow-y-auto space-y-3 text-xs leading-relaxed text-slate-700 pr-1">
                  {activeSection.summary && (
                    <div className="p-3 bg-amber-50/80 rounded-xl border-l-4 border-[#800020] text-slate-800 italic font-medium">
                      {activeSection.summary}
                    </div>
                  )}

                  <div className="prose prose-xs max-w-none text-slate-800 space-y-2 whitespace-pre-wrap">
                    {editedSections[activeSection.topic] !== undefined
                      ? editedSections[activeSection.topic]
                      : activeSection.prediction.replace(/^##\s+.+$/m, "").replace(/^\*\*Evidence Level:\*\*.+$/m, "").trim()}
                  </div>

                  <div className="pt-3 border-t flex justify-end">
                    <button
                      type="button"
                      onClick={() => setEditorMode("edit")}
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-300 text-slate-700 hover:bg-slate-50 flex items-center gap-1.5"
                    >
                      <i className="fa-solid fa-pen-to-square text-[#800020]"></i>
                      <span>Edit Prediction Text</span>
                    </button>
                  </div>
                </div>
              ) : (
                /* EDIT MODE: Textarea & Save Controls */
                <div className="flex-1 flex flex-col">
                  {/* Original Draft vs AI Revised Toggle */}
                  {activeSection.original_draft && activeSection.status !== "templated" && (
                    <div className="flex items-center justify-between mb-2">
                      <button
                        type="button"
                        onClick={() =>
                          setViewingOriginalDraft((prev) => ({
                            ...prev,
                            [activeSection.topic]: !prev[activeSection.topic],
                          }))
                        }
                        className="text-[0.6875rem] font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
                      >
                        <i className="fa-solid fa-code-compare"></i>
                        {viewingOriginalDraft[activeSection.topic] ? "Show Active Text" : "View Original Rule Draft"}
                      </button>

                      {viewingOriginalDraft[activeSection.topic] && (
                        <button
                          type="button"
                          onClick={() => {
                            setEditedSections((prev) => ({
                              ...prev,
                              [activeSection.topic]: activeSection.original_draft || "",
                            }));
                            setViewingOriginalDraft((prev) => ({ ...prev, [activeSection.topic]: false }));
                          }}
                          className="text-[0.6875rem] font-bold text-amber-700 hover:underline"
                        >
                          Revert to Rule Draft
                        </button>
                      )}
                    </div>
                  )}

                  <textarea
                    value={
                      viewingOriginalDraft[activeSection.topic]
                        ? activeSection.original_draft
                        : editedSections[activeSection.topic] !== undefined
                        ? editedSections[activeSection.topic]
                        : activeSection.prediction
                    }
                    readOnly={viewingOriginalDraft[activeSection.topic]}
                    onChange={(e) => {
                      const val = e.target.value;
                      setEditedSections((prev) => ({
                        ...prev,
                        [activeSection.topic]: val,
                      }));
                    }}
                    rows={12}
                    className="w-full flex-1 p-3 text-xs leading-relaxed rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-[#800020]/20 font-sans"
                    placeholder="Enter or refine the prediction narrative..."
                  />

                  {/* Section Actions */}
                  <div className="flex items-center justify-between gap-2 pt-2 mt-2 border-t border-slate-100">
                    <button
                      type="button"
                      onClick={() => handleRegenerateSection(activeSection.topic)}
                      disabled={sectionRegenerating === activeSection.topic}
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all flex items-center gap-1.5"
                      style={{ color: "#92400e", background: "#fffbeb", borderColor: "#fde68a" }}
                    >
                      {sectionRegenerating === activeSection.topic ? (
                        <LoadingSpinner />
                      ) : (
                        <i className="fa-solid fa-arrows-rotate"></i>
                      )}
                      <span>Regenerate Section</span>
                    </button>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => setEditorMode("read")}
                        className="px-3 py-1.5 rounded-lg border text-xs font-semibold text-slate-600 hover:bg-slate-50"
                      >
                        Done
                      </button>
                      <button
                        type="button"
                        onClick={() => handleSaveSectionEdit(activeSection.topic)}
                        disabled={
                          savingSection === activeSection.topic ||
                          editedSections[activeSection.topic] === undefined
                        }
                        className="px-4 py-1.5 rounded-lg text-xs font-semibold text-white transition-all flex items-center gap-1.5 shadow-sm disabled:opacity-50"
                        style={{ background: "#800020" }}
                      >
                        {savingSection === activeSection.topic ? (
                          <LoadingSpinner />
                        ) : (
                          <i className="fa-solid fa-floppy-disk"></i>
                        )}
                        <span>Save Changes</span>
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-8 text-center text-slate-400 text-xs">
              <i className="fa-solid fa-book-open text-3xl mb-3 text-slate-300"></i>
              <p className="font-medium text-slate-600">No predictions generated yet.</p>
              <p className="text-[0.6875rem] text-slate-400 mt-1">Click &quot;Generate Predictions from Chart&quot; above to start.</p>
            </div>
          )}
        </section>

        {/* ── RIGHT COLUMN: Live Generated PDF / Report Preview (lg:col-span-7) ── */}
        <section className="lg:col-span-7 flex flex-col items-center p-4 relative bg-[#f1f5f9] border-l border-[#e2e8f0] h-full overflow-y-auto">

          {/* Floating Controls Bar with Dual PDF Switcher */}
          <div
            className="w-full max-w-5xl rounded-xl shadow-md p-2.5 mb-3 flex flex-wrap items-center justify-between gap-2 z-10 sticky top-[65px] lg:top-0 no-print"
            style={{ background: "rgba(255, 255, 255, 0.96)", backdropFilter: "blur(8px)", border: "1px solid #ebdcb9" }}
          >
            {/* PDF View Mode Tabs */}
            <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg border border-slate-200">
              <button
                type="button"
                onClick={() => setActivePdfTab("prediction")}
                className={`px-3 py-1 rounded-md text-xs font-bold transition flex items-center gap-1.5 ${activePdfTab === "prediction" ? "bg-white text-[#800020] shadow-sm" : "text-slate-600 hover:text-slate-900"}`}
              >
                <i className="fa-solid fa-file-lines text-[#800020]"></i>
                <span>Prediction Report PDF</span>
              </button>
              <button
                type="button"
                onClick={() => setActivePdfTab("chart")}
                className={`px-3 py-1 rounded-md text-xs font-bold transition flex items-center gap-1.5 ${activePdfTab === "chart" ? "bg-white text-[#800020] shadow-sm" : "text-slate-600 hover:text-slate-900"}`}
              >
                <i className="fa-solid fa-chart-pie text-[#92400e]"></i>
                <span>Kundli Birth Chart PDF</span>
              </button>
            </div>

            {/* Action Buttons: Open, Print, Download PDF, Refresh */}
            <div className="flex items-center gap-2">
              {previewHtml && (
                <>
                  <button
                    type="button"
                    onClick={() => {
                      if (activePdfTab === "prediction" && previewHtml) {
                        const win = window.open("", "_blank");
                        if (win) {
                          win.document.write(previewHtml);
                          win.document.close();
                        }
                      } else if (chartPdfUrl) {
                        window.open(chartPdfUrl, "_blank");
                      }
                    }}
                    className="rounded-lg px-2.5 py-1 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 transition-all flex items-center gap-1 border border-slate-300"
                    id="btn-open-prediction"
                  >
                    <i className="fa-solid fa-up-right-from-square text-[0.625rem]"></i> Open
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      const iframe = document.querySelector("iframe");
                      if (iframe && iframe.contentWindow) {
                        iframe.contentWindow.focus();
                        iframe.contentWindow.print();
                      } else {
                        window.print();
                      }
                    }}
                    className="rounded-lg px-3 py-1.5 text-xs font-semibold shadow-sm flex items-center gap-1.5 transition-all text-white"
                    style={{ background: "#4f46e5" }}
                    id="btn-print-prediction"
                  >
                    <i className="fa-solid fa-print"></i> Print
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      const filename = predictionReport?.customer?.name
                        ? `${predictionReport.customer.name}_Jyotish_Predictions.pdf`
                        : "Jyotish_Predictions.pdf";
                      const downloadUrl = `${API}${compiledPdfUrl}?name=${encodeURIComponent(filename)}`;
                      const a = document.createElement("a");
                      a.href = downloadUrl;
                      a.target = "_blank";
                      a.download = filename;
                      document.body.appendChild(a);
                      a.click();
                      document.body.removeChild(a);
                    }}
                    className="rounded-lg px-3 py-1.5 text-xs font-semibold shadow-sm flex items-center gap-1.5 transition-all text-white btn-press"
                    style={{ background: "#800020" }}
                    id="btn-download-prediction-pdf"
                  >
                    <i className="fa-solid fa-download"></i> Download PDF
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      if (predictionReport) refreshPreview(predictionReport);
                    }}
                    className="rounded-lg px-2.5 py-1 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 transition-all flex items-center gap-1 border border-slate-300"
                    title="Refresh Preview"
                  >
                    <i className="fa-solid fa-arrows-rotate text-[0.625rem]"></i> Refresh
                  </button>
                </>
              )}
            </div>
          </div>

          {/* PDF Preview Canvas */}
          <div className="w-full max-w-5xl flex-1 flex flex-col items-center">
            {activePdfTab === "prediction" ? (
              previewUrl ? (
                <div className="w-full bg-white shadow-lg rounded-xl overflow-hidden border border-slate-200">
                  <iframe
                    src={previewUrl}
                    className="w-full h-[85vh] border-0"
                    title="Live Jyotish Prediction PDF Preview"
                  />
                </div>
              ) : (
                <div className="w-full h-[60vh] flex flex-col items-center justify-center p-8 bg-white rounded-xl border border-dashed border-slate-300 text-center shadow-sm">
                  <div className="w-16 h-16 rounded-full bg-amber-50 flex items-center justify-center text-3xl mb-4 text-[#800020]">
                    🕉️
                  </div>
                  <h3 className="text-base font-bold text-slate-800 mb-1">
                    Ready to Generate Jyotish Predictions
                  </h3>
                  <p className="text-xs text-slate-500 max-w-md mb-4">
                    Click <strong>&quot;Generate Predictions from Chart&quot;</strong> on the left to compute traditional Jyotish interpretations using Rulebook v2.0.
                  </p>
                  <button
                    type="button"
                    onClick={() => handleGenerateAll()}
                    className="px-4 py-2 rounded-xl text-white font-bold text-xs shadow-md transition-all flex items-center gap-2"
                    style={{ background: "linear-gradient(135deg, #800020, #92400e)" }}
                  >
                    <i className="fa-solid fa-wand-magic-sparkles"></i> Generate Complete Report
                  </button>
                </div>
              )
            ) : (
              /* Birth Chart PDF Tab */
              chartPdfUrl ? (
                <div className="w-full bg-white shadow-lg rounded-xl overflow-hidden border border-slate-200">
                  <iframe
                    src={chartPdfUrl}
                    className="w-full h-[85vh] border-0"
                    title="Kundli Birth Chart PDF Preview"
                  />
                </div>
              ) : (
                <div className="w-full h-[60vh] flex flex-col items-center justify-center p-8 bg-white rounded-xl border border-dashed border-slate-300 text-center shadow-sm">
                  <i className="fa-solid fa-chart-pie text-4xl mb-3 text-amber-600"></i>
                  <h3 className="text-base font-bold text-slate-800 mb-1">
                    Kundli Birth Chart PDF
                  </h3>
                  <p className="text-xs text-slate-500 max-w-md mb-4">
                    The birth chart PDF will appear here once generated from the client details.
                  </p>
                </div>
              )
            )}
          </div>
        </section>
      </main>

      {/* ── AI Settings Modal ── */}
      {aiSettingsOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-amber-200">
            <div className="flex items-center justify-between pb-3 border-b mb-4">
              <h3 className="font-bold text-sm text-[#800020] flex items-center gap-2">
                <i className="fa-solid fa-brain text-amber-600"></i> AI Engine Configuration
              </h3>
              <button onClick={() => setAiSettingsOpen(false)} className="text-slate-400 hover:text-slate-600">
                <i className="fa-solid fa-xmark"></i>
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Preferred AI Provider</label>
                <select
                  value={selectedProvider}
                  onChange={(e) => {
                    const p = e.target.value;
                    setSelectedProvider(p);
                    const pData = aiConfig?.providers.find((item) => item.id === p);
                    if (pData) setSelectedModel(pData.default_model);
                  }}
                  className="w-full p-2 border rounded-lg bg-white"
                >
                  <option value="groq">Groq Cloud (Fast &amp; Free Tier)</option>
                  <option value="gemini">Google Gemini API (Free Tier)</option>
                  <option value="openrouter">OpenRouter (Free Tier Models)</option>
                  <option value="custom">Custom / Local OpenAI-Compatible</option>
                </select>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Model Name</label>
                <input
                  type="text"
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full p-2 border rounded-lg"
                  placeholder="e.g. llama-3.3-70b-versatile or gemini-1.5-flash"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">
                  API Key <span className="font-normal text-slate-400">(Stored safely on backend)</span>
                </label>
                <input
                  type="password"
                  value={apiKeyInput}
                  onChange={(e) => setApiKeyInput(e.target.value)}
                  className="w-full p-2 border rounded-lg"
                  placeholder={
                    selectedProvider === "groq"
                      ? "gsk_..."
                      : selectedProvider === "gemini"
                      ? "AIzaSy..."
                      : "Enter provider API key"
                  }
                />
                <p className="text-[0.625rem] text-slate-500 mt-1">
                  Note: If no key is entered, the system safely uses the verified rulebook engine draft without failing.
                </p>
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6 pt-3 border-t">
              <button
                type="button"
                onClick={() => setAiSettingsOpen(false)}
                className="px-3 py-1.5 rounded-lg border text-slate-600 hover:bg-slate-50 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveAiSettings}
                className="px-4 py-1.5 rounded-lg bg-[#800020] text-white text-xs font-semibold hover:bg-[#66001a]"
              >
                Save AI Configuration
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
