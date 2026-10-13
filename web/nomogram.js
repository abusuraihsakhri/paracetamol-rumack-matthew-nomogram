"use strict";
(function (root) {
  const patterns = ["acute", "repeated", "unknown", "modified_release"];
  function number(value, name) {
    if (typeof value !== "number" || !Number.isFinite(value) || value < 0) {
      throw new RangeError(name + " must be finite and nonnegative");
    }
    return value;
  }
  function lineAt(hours) {
    number(hours, "Hours");
    if (hours < 4 || hours > 24) throw new RangeError("Nomogram time range is 4–24 h");
    return 150 * Math.pow(2, -(hours - 4) / 4);
  }
  function evaluate(input) {
    const hours = number(input.hours, "Hours");
    const concentration = number(input.concentration, "Concentration");
    if (!patterns.includes(input.pattern)) throw new RangeError("Invalid ingestion pattern");
    if (typeof input.timeKnown !== "boolean" || typeof input.delayedAbsorption !== "boolean") {
      throw new TypeError("History flags must be booleans");
    }
    const reasons = [];
    if (!input.timeKnown) reasons.push("Ingestion time is unknown or unreliable.");
    if (input.pattern !== "acute") reasons.push("This ingestion pattern/formulation cannot be interpreted on this nomogram.");
    if (hours < 4) reasons.push("Samples before 4 h cannot be interpreted.");
    if (hours > 24) reasons.push("The nomogram is not applicable after 24 h.");
    const cautions = input.delayedAbsorption ? ["Possible delayed absorption; repeat levels and toxicology review may be needed."] : [];
    if (reasons.length) return {hours, concentration, status:"not_applicable", line:null, reasons, cautions,
      recommendation:"Do not rely on the nomogram. Seek urgent poison-center or toxicology assessment."};
    const line = lineAt(hours);
    const above = concentration >= line;
    return {hours, concentration, line, reasons, cautions,
      status:above ? "at_or_above_treatment_line" : "below_treatment_line",
      recommendation:above
        ? "At or above the 150-line: urgent assessment for N-acetylcysteine under local protocols."
        : "Below the 150-line: not sufficient alone to rule out toxicity; review history, follow-up and other clinical data."};
  }
  const api={lineAt,evaluate};
  if (typeof module !== "undefined" && module.exports) module.exports=api;
  root.Nomogram=api;
})(typeof window !== "undefined" ? window : globalThis);
