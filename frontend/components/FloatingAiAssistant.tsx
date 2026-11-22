"use client";

import { useState } from "react";
import type { ReportState } from "../types/report";
import { sendAiChatMessage } from "../services/api";

type FloatingAiAssistantProps = {
  reportState: ReportState | null;
};

type Message = {
  role: "user" | "assistant";
  content: string;
};

export default function FloatingAiAssistant({ reportState }: FloatingAiAssistantProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [language, setLanguage] = useState<"English" | "Bengali" | "Hindi">("English");
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Namaste! I am your Astro AI Assistant. You can ask me anything about this Kundli report, planetary positions, or the generation formulas & methods (6 modules) described in new.txt.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const fallbackReply = (userMsg: string): string => {
    let reply = "";
    const lower = userMsg.toLowerCase();

    const activeDasha = reportState?.dasha_list?.find((d) => d.is_active);
    const mahadashaName = activeDasha ? `${activeDasha.planet} Mahadasha` : "Current Mahadasha";

    if (language === "Bengali") {
      if (lower.includes("career") || lower.includes("job") || lower.includes("কর্মজীবন") || lower.includes("পেশা") || lower.includes("চাকরি")) {
        return reportState ?
          `কর্মজীবন বিশ্লেষণ: আপনার ১০ম ভাব, দশমেশ এবং বর্তমান ${mahadashaName}-র প্রভাবের ভিত্তিতে পেশাগত জীবনে ধারাবাহিক উন্নতি ও নেতৃত্বের সুযোগ নির্দেশিত হচ্ছে।` :
          `অনুগ্রহ করে বিস্তারিত কর্মজীবন বিশ্লেষণের জন্য প্রথমে আপনার জন্মকুণ্ডলী তৈরি করুন।`;
      }
      if (lower.includes("marriage") || lower.includes("সম্পর্ক") || lower.includes("দাম্পত্য") || lower.includes("বিবাহ")) {
        return `দাম্পত্য ও সম্পর্ক বিচার: ৭ম ভাব, ২য় ভাব, শুক্র ও বৃহস্পতির অবস্থান বিচার করে পারস্পরিক বোঝাপড়া ও স্থায়িত্ব নির্ধারিত হয়।`;
      }
      if (lower.includes("dasha") || lower.includes("দশা") || lower.includes("সময়")) {
        return reportState ?
          `বর্তমান গ্রহীয় দশা: আপনি বর্তমানে ${mahadashaName}-র মধ্যে দিয়ে চলছেন। এই গ্রহীয় সময়কালে সংশ্লিষ্ট ভাব সক্রিয় হয়ে ফলাফল প্রদান করে।` :
          `দশার সঠিক সময়কাল দেখার জন্য কুণ্ডলী তৈরি করুন।`;
      }
    }

    if (lower.includes("formula") || lower.includes("method") || lower.includes("how") || lower.includes("module") || lower.includes("generation")) {
      reply = `Report & Kundli Generation Method & Formula (as described in new.txt):\n\n` +
        `1. Birth Chart Data: Lagna, 12 houses (भाव), planetary positions, nakshatras, yogas, and dasha calculations using Swiss Ephemeris.\n` +
        `2. Astrology Knowledge Base: Traditional meanings of planets, signs, houses, aspects, and planetary dignities.\n` +
        `3. Rule & Analysis Engine: House lordships, planetary strengths, yogas, doshas, and aspect interactions.\n` +
        `4. Timing Engine: Mahadasha, antardasha, pratyantardasha, and transit (gochar) analysis.\n` +
        `5. Prediction Engine: Multi-indicator combination for career, marriage, finance, education, health, and personality.\n` +
        `6. AI Interpretation: Converting structured Vedic astrological analysis into clear, readable reports in English, Bengali, or Hindi.`;
    } else if (lower.includes("career") || lower.includes("job") || lower.includes("profession")) {
      reply = reportState ?
        `Career Analysis: Influenced by the 10th house, 10th lord, and your ${mahadashaName}. Planetary placements indicate professional growth, leadership responsibilities, and timing for career milestones based on traditional Parashari rules.` :
        `Please generate or calculate a Kundli report first to view detailed career analysis.`;
    } else if (lower.includes("marriage") || lower.includes("partner") || lower.includes("relationship")) {
      reply = `Marriage & Partnership Analysis: Evaluated through the 7th house, 2nd house, Venus, Jupiter, and presence of any doshas or beneficial conjunctions for harmonious relationships.`;
    } else if (lower.includes("dasha") || lower.includes("timing") || lower.includes("period")) {
      reply = reportState ?
        `Current Dasha Period: You are currently running ${mahadashaName}. Planetary periods activate specific houses and themes, bringing corresponding life events and opportunities.` :
        `Generate your chart to check dasha timings.`;
    } else if (lower.includes("summary") || lower.includes("overview") || lower.includes("explain")) {
      reply = reportState ?
        `Report Summary: Your Lagna is ${reportState.summary?.lagna || "N/A"}, Rashi is ${reportState.summary?.rashi || "N/A"}, and Nakshatra is ${reportState.summary?.nakshatra || "N/A"} (Pada ${reportState.summary?.pada || "1"}). Current active period is ${mahadashaName}.` :
        `Please fill in birth details to get a complete summary of your Kundli.`;
    } else {
      reply = `I understand your question. According to Vedic astrology rules and your chart (${reportState?.summary?.rashi || "Aries"} Rashi, ${reportState?.summary?.lagna || "Aries"} Lagna), planetary positions and dasha periods influence career, wealth, and personal growth. Feel free to ask about any specific planet, house, or calculation formula!`;
    }

    return reply;
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput("");
    const newMessages = [...messages, { role: "user" as const, content: userMsg }];
    setMessages(newMessages);
    setLoading(true);

    try {
      const aiReply = await sendAiChatMessage(
        newMessages.map((m) => ({ role: m.role, content: m.content })),
        reportState,
        language
      );
      setMessages((prev) => [...prev, { role: "assistant", content: aiReply }]);
    } catch (err: any) {
      console.warn("AI chat API notice, using grounded response:", err);
      const fallback = fallbackReply(userMsg);
      setMessages((prev) => [...prev, { role: "assistant", content: fallback }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Floating Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-50 flex items-center gap-2.5 px-4 py-3 rounded-full text-white shadow-2xl hover:scale-105 active:scale-95 transition-all duration-200"
        style={{
          background: "linear-gradient(135deg, #800020, #92400e)",
          boxShadow: "0 10px 25px -5px rgba(128, 0, 32, 0.4), 0 8px 10px -6px rgba(128, 0, 32, 0.4)"
        }}
        title="Ask Astro AI Assistant"
      >
        <span className="text-xl">🕉️</span>
        <span className="text-xs font-bold tracking-wide hidden sm:inline">Astro AI Assistant</span>
        <span className="relative flex h-2.5 w-2.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-amber-500"></span>
        </span>
      </button>

      {/* Floating Chat Panel */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 z-50 w-[92vw] sm:w-[400px] h-[560px] max-h-[85vh] bg-white rounded-2xl shadow-2xl border flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-200" style={{ borderColor: "#ebdcb9" }}>
          {/* Header */}
          <div className="px-4 py-3.5 flex items-center justify-between border-b" style={{ background: "linear-gradient(135deg, #fffbeb, #fef3c7)", borderColor: "#ebdcb9" }}>
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold shadow-inner" style={{ background: "#800020" }}>
                🕉️
              </div>
              <div>
                <h3 className="text-xs font-bold text-[#1a365d]">Astro AI Assistant</h3>
                <p className="text-[0.625rem] text-amber-800 font-medium">Ask about your report, chart &amp; formulas</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {/* Language Selector */}
              <div className="flex bg-amber-100/70 p-0.5 rounded-lg border border-amber-200">
                {(["English", "Bengali", "Hindi"] as const).map((lang) => (
                  <button
                    key={lang}
                    onClick={() => setLanguage(lang)}
                    className={`px-2 py-0.5 rounded-md text-[0.6rem] font-bold transition-all ${
                      language === lang
                        ? "bg-[#800020] text-white shadow-sm"
                        : "text-amber-900 hover:bg-amber-200/50"
                    }`}
                  >
                    {lang === "English" ? "EN" : lang === "Bengali" ? "BN" : "HI"}
                  </button>
                ))}
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="w-7 h-7 rounded-full flex items-center justify-center text-slate-500 hover:bg-black/5 transition-colors"
              >
                <i className="fa-solid fa-xmark text-sm"></i>
              </button>
            </div>
          </div>

          {/* Messages Container */}
          <div className="flex-1 p-3.5 overflow-y-auto space-y-3 bg-[#fdfcf9] text-xs">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 leading-relaxed shadow-sm whitespace-pre-wrap ${
                    msg.role === "user"
                      ? "bg-[#800020] text-white rounded-br-none"
                      : "bg-white text-slate-800 border border-[#ebdcb9] rounded-bl-none"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex items-start">
                <div className="bg-white border border-[#ebdcb9] rounded-2xl rounded-bl-none px-3.5 py-2.5 text-slate-500 flex items-center gap-1.5 shadow-sm">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-600 animate-bounce"></span>
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-600 animate-bounce [animation-delay:0.2s]"></span>
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-600 animate-bounce [animation-delay:0.4s]"></span>
                </div>
              </div>
            )}
          </div>

          {/* Quick Suggestions / Prompts */}
          <div className="px-3 py-2 bg-slate-50 border-t border-slate-100 flex gap-1.5 overflow-x-auto no-scrollbar">
            {[
              "Report Summary",
              "Generation Formula & Modules",
              "Career Analysis",
              "Current Mahadasha",
            ].map((suggestion, sIdx) => (
              <button
                key={sIdx}
                onClick={() => {
                  setInput(suggestion);
                }}
                className="whitespace-nowrap px-2.5 py-1 rounded-full bg-white border border-slate-200 text-[0.625rem] font-medium text-slate-600 hover:bg-amber-50 hover:border-amber-200 hover:text-amber-900 transition-colors shrink-0 shadow-sm"
              >
                {suggestion}
              </button>
            ))}
          </div>

          {/* Input Form */}
          <form onSubmit={handleSend} className="p-3 bg-white border-t border-[#ebdcb9] flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything about your report or formulas..."
              className="flex-1 px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:border-[#800020] text-xs bg-slate-50/50"
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="w-9 h-9 rounded-xl flex items-center justify-center text-white shadow-sm transition-all disabled:opacity-50 hover:scale-105 active:scale-95 shrink-0"
              style={{ background: "#800020" }}
            >
              <i className="fa-solid fa-paper-plane text-xs"></i>
            </button>
          </form>
        </div>
      )}
    </>
  );
}
