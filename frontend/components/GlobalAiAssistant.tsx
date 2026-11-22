"use client";

import { useEffect, useState } from "react";
import FloatingAiAssistant from "./FloatingAiAssistant";
import type { ReportState } from "../types/report";

export default function GlobalAiAssistant() {
  const [reportState, setReportState] = useState<ReportState | null>(null);

  useEffect(() => {
    const syncState = () => {
      try {
        const stored =
          sessionStorage.getItem("last_report_state") ||
          sessionStorage.getItem("latest_report_data") ||
          sessionStorage.getItem("pending_prediction_details");
        if (stored) {
          const parsed = JSON.parse(stored);
          setReportState(parsed);
        }
      } catch (err) {
        // ignore parse errors
      }
    };

    syncState();
    window.addEventListener("storage", syncState);
    window.addEventListener("kundli_report_updated", syncState);

    return () => {
      window.removeEventListener("storage", syncState);
      window.removeEventListener("kundli_report_updated", syncState);
    };
  }, []);

  return <FloatingAiAssistant reportState={reportState} />;
}
