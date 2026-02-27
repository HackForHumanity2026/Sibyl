/**
 * IFRS S1/S2 Paragraph Registry — bundled in the frontend for hover tooltips.
 * All 44 paragraphs from backend/data/ifrs/paragraph_registry.json, plus
 * section-level aliases so prefix matching works for abbreviated IDs.
 */

export interface ParagraphInfo {
  section: string;
  requirement_text: string;
  standard: "S1" | "S2";
  pillar: string;
}

export const PARAGRAPH_REGISTRY: Record<string, ParagraphInfo> = {
  // ── IFRS S1 Governance ──────────────────────────────────────────────────────
  "S1.26": {
    standard: "S1", pillar: "governance", section: "Governance Objective",
    requirement_text: "The objective of sustainability-related financial disclosures on governance is to enable users to understand the governance processes, controls and procedures an entity uses to monitor, manage and oversee sustainability-related risks and opportunities.",
  },
  "S1.27": {
    standard: "S1", pillar: "governance", section: "Governance Disclosures",
    requirement_text: "An entity shall disclose information about the governance body(s) or individual(s) responsible for oversight of sustainability-related risks and opportunities, and management's role in the governance processes, controls and procedures used to monitor, manage and oversee sustainability-related risks and opportunities.",
  },
  "S1.27(a)": {
    standard: "S1", pillar: "governance", section: "Governance Body Oversight",
    requirement_text: "Disclose information about the governance body(s) or individual(s) responsible for oversight of sustainability-related risks and opportunities.",
  },
  "S1.27(a)(i)": {
    standard: "S1", pillar: "governance", section: "Terms of Reference",
    requirement_text: "How responsibilities for sustainability-related risks and opportunities are reflected in the terms of reference, mandates, role descriptions and other related policies applicable to that body(s) or individual(s).",
  },
  "S1.27(a)(ii)": {
    standard: "S1", pillar: "governance", section: "Skills and Competencies",
    requirement_text: "How the body(s) or individual(s) determines whether appropriate skills and competencies are available or will be developed to oversee strategies designed to respond to sustainability-related risks and opportunities.",
  },
  "S1.27(a)(iii)": {
    standard: "S1", pillar: "governance", section: "Reporting Frequency",
    requirement_text: "How and how often the body(s) or individual(s) is informed about sustainability-related risks and opportunities.",
  },
  "S1.27(a)(iv)": {
    standard: "S1", pillar: "governance", section: "Strategy Integration",
    requirement_text: "How the body(s) or individual(s) takes into account sustainability-related risks and opportunities when overseeing the entity's strategy, its decisions on major transactions and its risk management processes and related policies, including whether the body(s) or individual(s) has considered trade-offs between sustainability-related and other risks.",
  },
  "S1.27(a)(v)": {
    standard: "S1", pillar: "governance", section: "Target Oversight and Remuneration",
    requirement_text: "How the body(s) or individual(s) oversees the setting of targets related to sustainability-related risks and opportunities, and monitors progress towards those targets, including whether and how related performance metrics are included in remuneration policies.",
  },
  "S1.27(b)": {
    standard: "S1", pillar: "governance", section: "Management Role",
    requirement_text: "Management's role in the governance processes, controls and procedures used to monitor, manage and oversee sustainability-related risks and opportunities.",
  },
  "S1.27(b)(i)": {
    standard: "S1", pillar: "governance", section: "Management Delegation",
    requirement_text: "Whether the entity has assigned responsibility for managing sustainability-related risks and opportunities to a specific management-level position or management-level committee, and whether that person or committee reports to the governance body.",
  },
  "S1.27(b)(ii)": {
    standard: "S1", pillar: "governance", section: "Management Controls",
    requirement_text: "The related controls and procedures used to support the oversight of sustainability-related risks and opportunities, and how these integrate with other internal functions.",
  },

  // ── IFRS S1 Strategy ────────────────────────────────────────────────────────
  "S1.33": {
    standard: "S1", pillar: "strategy", section: "Strategy and Decision-Making",
    requirement_text: "An entity shall disclose information to enable users of general purpose financial reports to understand the effects of significant sustainability-related risks and opportunities on its strategy and decision-making.",
  },

  // ── IFRS S1 Risk Management ─────────────────────────────────────────────────
  "S1.38": {
    standard: "S1", pillar: "risk_management", section: "Risk Management Objective",
    requirement_text: "The objective of sustainability-related financial disclosures on risk management is to enable users to understand the processes an entity uses to identify, assess, prioritise and monitor sustainability-related risks and opportunities.",
  },
  "S1.41": {
    standard: "S1", pillar: "risk_management", section: "Risk Management Processes",
    requirement_text: "An entity shall disclose information about the processes and related policies the entity uses to identify, assess, prioritise and monitor sustainability-related risks and opportunities, and how those processes are integrated into overall risk management.",
  },
  "S1.41(a)": {
    standard: "S1", pillar: "risk_management", section: "Risk Identification",
    requirement_text: "The processes and related policies the entity uses to identify sustainability-related risks and opportunities.",
  },
  "S1.41(b)": {
    standard: "S1", pillar: "risk_management", section: "Risk Assessment",
    requirement_text: "The processes the entity uses to assess, prioritise and monitor sustainability-related risks and opportunities.",
  },
  "S1.41(c)": {
    standard: "S1", pillar: "risk_management", section: "Risk Monitoring Input Parameters",
    requirement_text: "The inputs used to identify, assess, prioritise and monitor sustainability-related risks and opportunities.",
  },
  "S1.41(d)": {
    standard: "S1", pillar: "risk_management", section: "Integration with Overall Risk Management",
    requirement_text: "How the processes the entity uses to identify, assess, prioritise and monitor sustainability-related risks and opportunities are integrated into and inform the entity's overall risk management.",
  },
  "S1.42": {
    standard: "S1", pillar: "risk_management", section: "Changes from Prior Period",
    requirement_text: "Whether and how the processes described in paragraph 41 have changed compared with the prior period.",
  },

  // ── IFRS S1 Metrics & Targets ───────────────────────────────────────────────
  "S1.46": {
    standard: "S1", pillar: "metrics_targets", section: "Metrics Disclosure",
    requirement_text: "An entity shall disclose quantitative and qualitative information about its progress towards any targets it has set, and any targets it is required to meet by law or regulation, to enable users to assess the entity's performance and monitor progress.",
  },

  // ── IFRS S2 Governance ──────────────────────────────────────────────────────
  "S2.5": {
    standard: "S2", pillar: "governance", section: "Climate Governance Objective",
    requirement_text: "The objective of climate-related financial disclosures on governance is to enable users to understand the governance processes, controls and procedures an entity uses to monitor, manage and oversee climate-related risks and opportunities.",
  },
  "S2.6": {
    standard: "S2", pillar: "governance", section: "Climate Governance Body Oversight",
    requirement_text: "Disclose information about the governance body(s) or individual(s) responsible for oversight of climate-related risks and opportunities, including competencies, reporting frequency, strategy integration, and target oversight with remuneration links.",
  },
  "S2.7": {
    standard: "S2", pillar: "governance", section: "Climate Management Role",
    requirement_text: "Management's role in the governance processes, controls and procedures used to monitor, manage and oversee climate-related risks and opportunities.",
  },

  // ── IFRS S2 Strategy ────────────────────────────────────────────────────────
  "S2.14": {
    standard: "S2", pillar: "strategy", section: "Strategy and Decision-Making",
    requirement_text: "An entity shall disclose information that enables users to understand the effects of climate-related risks and opportunities on its strategy and decision-making, including transition plans.",
  },
  "S2.14(a)": {
    standard: "S2", pillar: "strategy", section: "Climate Response Strategy",
    requirement_text: "How the entity is responding to climate-related risks and opportunities in its strategy and decision-making.",
  },
  "S2.14(a)(i)": {
    standard: "S2", pillar: "strategy", section: "Resource Allocation Changes",
    requirement_text: "How the entity is responding to climate-related risks and opportunities in its strategy and decision-making, including how it plans to change resource allocation.",
  },
  "S2.14(a)(ii)": {
    standard: "S2", pillar: "strategy", section: "Direct Mitigation and Adaptation",
    requirement_text: "Direct mitigation and adaptation efforts the entity is undertaking.",
  },
  "S2.14(a)(iii)": {
    standard: "S2", pillar: "strategy", section: "Indirect Mitigation",
    requirement_text: "Indirect mitigation and adaptation efforts including value chain engagement and carbon offsets.",
  },
  "S2.14(a)(iv)": {
    standard: "S2", pillar: "strategy", section: "Transition Plan",
    requirement_text: "An entity shall disclose its transition plan, including information about: key assumptions used in developing its transition plan; dependencies on which the entity's transition plan relies; the timeline for achieving transition plan objectives.",
  },
  "S2.14(a)(v)": {
    standard: "S2", pillar: "strategy", section: "Target Achievement Plans",
    requirement_text: "How the entity plans to achieve any climate-related targets it has set or is required to meet by law or regulation.",
  },
  "S2.14(b)": {
    standard: "S2", pillar: "strategy", section: "Resourcing",
    requirement_text: "How the entity is resourcing its climate-related strategy and decision-making.",
  },
  "S2.14(c)": {
    standard: "S2", pillar: "strategy", section: "Progress on Prior Plans",
    requirement_text: "Quantitative and qualitative information about progress of plans disclosed in prior periods.",
  },

  // ── IFRS S2 Risk Management ─────────────────────────────────────────────────
  "S2.24": {
    standard: "S2", pillar: "risk_management", section: "Climate Risk Management Objective",
    requirement_text: "The objective of climate-related financial disclosures on risk management is to enable users to understand the processes an entity uses to identify, assess, prioritise and monitor climate-related risks and opportunities.",
  },
  "S2.25": {
    standard: "S2", pillar: "risk_management", section: "Climate Risk Management Processes",
    requirement_text: "An entity shall disclose information about its processes for identifying, assessing, prioritising and monitoring climate-related risks and opportunities.",
  },
  "S2.25(a)": {
    standard: "S2", pillar: "risk_management", section: "Climate Risk Identification",
    requirement_text: "The processes and related policies the entity uses to identify climate-related risks and opportunities.",
  },
  "S2.25(b)": {
    standard: "S2", pillar: "risk_management", section: "Climate Risk Assessment",
    requirement_text: "The processes the entity uses to assess, prioritise and monitor climate-related risks and opportunities.",
  },
  "S2.25(c)": {
    standard: "S2", pillar: "risk_management", section: "Climate Risk Inputs",
    requirement_text: "The inputs used to identify, assess, prioritise and monitor climate-related risks and opportunities.",
  },
  "S2.26": {
    standard: "S2", pillar: "risk_management", section: "Climate Risk Integration",
    requirement_text: "How the processes the entity uses to identify, assess, prioritise and monitor climate-related risks and opportunities are integrated into and inform the entity's overall risk management.",
  },

  // ── IFRS S2 Metrics & Targets ───────────────────────────────────────────────
  "S2.27": {
    standard: "S2", pillar: "metrics_targets", section: "Climate Metrics Objective",
    requirement_text: "The objective of climate-related financial disclosures on metrics and targets is to enable users to understand an entity's performance in relation to its climate-related risks and opportunities, including progress towards any climate-related targets it has set.",
  },
  "S2.28": {
    standard: "S2", pillar: "metrics_targets", section: "Climate-related Metrics",
    requirement_text: "An entity shall disclose climate-related metrics including emission intensity, internal carbon prices, and climate-related remuneration.",
  },
  "S2.29": {
    standard: "S2", pillar: "metrics_targets", section: "GHG Emissions Disclosure",
    requirement_text: "An entity shall disclose its absolute gross greenhouse gas emissions generated during the reporting period, expressed as metric tonnes of CO2 equivalent, classified as Scope 1, Scope 2, and Scope 3 emissions.",
  },
  "S2.29(a)": {
    standard: "S2", pillar: "metrics_targets", section: "Absolute GHG Emissions",
    requirement_text: "An entity shall disclose its absolute gross greenhouse gas emissions generated during the reporting period, expressed as metric tonnes of CO2 equivalent, classified as Scope 1, Scope 2, and Scope 3 emissions.",
  },
  "S2.29(a)(i)": {
    standard: "S2", pillar: "metrics_targets", section: "Scope 1 Emissions",
    requirement_text: "Scope 1 greenhouse gas emissions — direct emissions from sources that are owned or controlled by the entity.",
  },
  "S2.29(a)(ii)": {
    standard: "S2", pillar: "metrics_targets", section: "Scope 2 Emissions",
    requirement_text: "Scope 2 greenhouse gas emissions — indirect emissions from the generation of purchased or acquired energy.",
  },
  "S2.29(a)(iii)": {
    standard: "S2", pillar: "metrics_targets", section: "Scope 3 Emissions",
    requirement_text: "Scope 3 greenhouse gas emissions by category, measured in accordance with the GHG Protocol Corporate Value Chain Standard.",
  },
  "S2.29(b)": {
    standard: "S2", pillar: "metrics_targets", section: "Industry-Based Metrics",
    requirement_text: "The industry-based metrics associated with the entity's business model and activities, as set out in the Industry-based Guidance on implementing IFRS S2.",
  },
  "S2.29(c)": {
    standard: "S2", pillar: "metrics_targets", section: "Entity-Specific Metrics",
    requirement_text: "The metrics the entity uses to measure and monitor climate-related risks and opportunities and its performance in managing those risks and opportunities.",
  },
  "S2.29(e)": {
    standard: "S2", pillar: "metrics_targets", section: "Internal Carbon Pricing",
    requirement_text: "If the entity uses internal carbon prices, disclose how the entity is applying the carbon price in decision-making.",
  },
  "S2.29(g)": {
    standard: "S2", pillar: "metrics_targets", section: "Climate-related Remuneration",
    requirement_text: "The percentage of executive management remuneration recognized in the current period that is linked to climate-related considerations.",
  },
  "S2.30": {
    standard: "S2", pillar: "metrics_targets", section: "GHG Measurement Approach",
    requirement_text: "An entity shall disclose the measurement approach, inputs and assumptions used to measure GHG emissions.",
  },
  "S2.31": {
    standard: "S2", pillar: "metrics_targets", section: "Consolidation Approach",
    requirement_text: "An entity shall disclose the approach used to determine the consolidation of GHG emissions (equity share, financial control, or operational control).",
  },
  "S2.33": {
    standard: "S2", pillar: "metrics_targets", section: "Climate Targets",
    requirement_text: "An entity shall disclose each climate-related target it has set, including information about metrics, base period, interim and ultimate milestones, and progress.",
  },
  "S2.33(a)": {
    standard: "S2", pillar: "metrics_targets", section: "Target Metric",
    requirement_text: "The metric used to set the target, including whether it is an absolute or intensity-based metric.",
  },
  "S2.33(b)": {
    standard: "S2", pillar: "metrics_targets", section: "Target Scope",
    requirement_text: "The objective of the target, including the applicable scope of the target.",
  },
  "S2.33(c)": {
    standard: "S2", pillar: "metrics_targets", section: "Target Period",
    requirement_text: "The time period over which the target applies.",
  },
  "S2.33(d)": {
    standard: "S2", pillar: "metrics_targets", section: "Target Baseline",
    requirement_text: "The base period from which progress is measured.",
  },
  "S2.33(e)": {
    standard: "S2", pillar: "metrics_targets", section: "Target Milestones",
    requirement_text: "Any milestones and interim targets.",
  },
  "S2.33(f)": {
    standard: "S2", pillar: "metrics_targets", section: "Target Performance",
    requirement_text: "Performance against each target and an analysis of trends or changes in performance.",
  },
  "S2.33(g)": {
    standard: "S2", pillar: "metrics_targets", section: "GHG Net-Zero Targets",
    requirement_text: "If the target is a GHG emissions target, whether the target has been validated by a third party, and whether the third party uses a particular methodology.",
  },
  "S2.34": {
    standard: "S2", pillar: "metrics_targets", section: "GHG Emission Targets",
    requirement_text: "For GHG emission targets, disclose the targeted reduction in absolute emissions or intensity, whether the target is gross or net (including role of offsets), and scope coverage.",
  },
  "S2.35": {
    standard: "S2", pillar: "metrics_targets", section: "Target Baseline and Milestones",
    requirement_text: "For each target, disclose the base period, baseline value, target value, and interim milestones.",
  },
  "S2.36": {
    standard: "S2", pillar: "metrics_targets", section: "Target Progress",
    requirement_text: "For each target, disclose performance against the target and analysis of trends or changes in the entity's performance.",
  },
};

/**
 * Look up a paragraph by ID.
 * Strategy:
 *  1. Exact match (fast path)
 *  2. Case-insensitive exact match
 *  3. Prefix match — e.g. "S1.27" finds the first key starting with "S1.27"
 *     so section-level IDs without sub-letters always resolve to something.
 */
export function getParagraphInfo(paragraphId: string): ParagraphInfo | undefined {
  // 1. Exact
  if (PARAGRAPH_REGISTRY[paragraphId]) return PARAGRAPH_REGISTRY[paragraphId];

  // 2. Case-insensitive exact
  const lower = paragraphId.toLowerCase();
  const allKeys = Object.keys(PARAGRAPH_REGISTRY);
  const exactCI = allKeys.find((k) => k.toLowerCase() === lower);
  if (exactCI) return PARAGRAPH_REGISTRY[exactCI];

  // 3. Prefix match — find shortest key that starts with this ID
  // e.g. "S1.27" → matches "S1.27", "S1.27(a)", "S1.27(a)(i)"; prefers "S1.27"
  const prefix = paragraphId;
  const prefixMatches = allKeys.filter(
    (k) => k.startsWith(prefix) || k.toLowerCase().startsWith(lower)
  );
  if (prefixMatches.length > 0) {
    // Return the shortest (most general) match
    prefixMatches.sort((a, b) => a.length - b.length);
    return PARAGRAPH_REGISTRY[prefixMatches[0]];
  }

  return undefined;
}
