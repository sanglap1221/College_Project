export interface PredictionFactor {
  factor: string;
  interpretation: string;
  rule_id: string;
  simple_explanation?: Record<string, string>;
  advanced_explanation?: Record<string, string>;
  why_matters?: Record<string, string>;
  example?: Record<string, string>;
  limitations?: Record<string, string>;
}

export interface PredictionValidation {
  rulebook_consistency?: string;
  chart_evidence_consistency?: string;
  unsupported_claims?: string[];
  contradictions?: string[];
  missing_data?: string[];
  warnings?: string[];
}

export interface PredictionSection {
  topic: string;
  title: string;
  evidence_level: "Limited" | "Moderate" | "Convergent" | string;
  lean: string;
  explanation: string;
  counts?: {
    supportive: number;
    challenging: number;
    mixed: number;
    independent_groups: number;
  };
  overview?: string;
  themes?: string[];
  challenges?: string[];
  basis_ids?: string[];
  summary: string;
  prediction: string;
  original_draft?: string;
  supporting_factors?: PredictionFactor[];
  challenging_factors?: PredictionFactor[];
  why_this?: {
    placement_meaning?: Record<string, string>;
    involved_factors?: Record<string, string>;
    life_themes?: Record<string, string>;
    relevance?: Record<string, string>;
    modifying_factors?: Record<string, string>;
    synthesis?: Record<string, string>;
    explained_factors?: any[];
  };
  translations?: Record<string, {
    title: string;
    overview: string;
    themes: string[];
    challenges: string[];
    summary: string;
    prediction: string;
    why_this?: {
      placement_meaning?: string;
      involved_factors?: string;
      life_themes?: string;
      relevance?: string;
      modifying_factors?: string;
      synthesis?: string;
    };
  }>;
  timing?: any[];
  status: "reviewed" | "ai_rewritten_audited" | "templated" | "templated_fallback" | "manual_edited" | string;
  review_status?: string;
  notes?: string[];
  rule_ids?: string[];
  limitations?: string[];
  validation?: PredictionValidation;
}

export interface PredictionReport {
  report_id: string;
  chart_id?: string;
  chart_hash?: string;
  is_outdated?: boolean;
  ruleset: {
    id: string;
    version: string;
    house_system: string;
    ayanamsa: string;
  };
  reference_date: string;
  language: string;
  generated_at: string;
  executive_overview?: string;
  include_technical_appendix?: boolean;
  customer: {
    name: string;
    dob: string;
    time: string;
    place: string;
  };
  chart_overview: {
    lagna_sign_name: string;
    lagna_sign_index: number;
    lagna_degree: number;
    rashi_sign_name: string;
    rashi_sign_index: number;
    nakshatra_name: string;
    nakshatra_pada: number;
    nakshatra_lord: string;
    ayanamsa: number;
    gana?: string;
    varna?: string;
  };
  sections: PredictionSection[];
  yoga_trace?: any[];
  all_yogas_checked?: number;
  dasha_summary?: Array<{
    level: string;
    lord: string;
    start: string;
    end: string;
  }>;
  ai_meta?: {
    used_ai: boolean;
    provider: string;
    model: string;
  };
  limitations: string[];
}

export interface AiProviderInfo {
  id: string;
  name: string;
  models: string[];
  default_model: string;
  has_key: boolean;
  is_active: boolean;
}

export interface AiConfigResponse {
  active_provider: string;
  active_model: string;
  is_configured: boolean;
  providers: AiProviderInfo[];
}
