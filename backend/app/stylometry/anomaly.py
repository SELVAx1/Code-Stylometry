from app.stylometry.extractor import FeatureExtractor
from app.stylometry.comparator import StyleComparator

STYLE_FEATURES = {
    "avg_line_length", "max_line_length", "blank_line_ratio",
    "uses_bits_stdc", "uses_iostream", "individual_includes",
    "brace_same_line_ratio", "spaces_around_operators", "space_after_comma",
    "space_before_paren", "uses_endl", "uses_newline_char", "uses_printf",
    "uses_cout", "uses_long_long", "uses_int64", "uses_auto", "uses_typedef",
    "uses_using_alias", "uses_define", "for_ratio", "while_ratio",
    "range_for_ratio", "avg_identifier_length", "single_char_var_ratio",
    "underscore_naming_ratio", "camel_case_ratio", "comment_density",
    "uses_pb", "uses_ll_macro", "has_template_header",
    "uses_cin", "uses_scanf", "uses_fast_io", "has_return_0",
    "uses_tabs", "whitespace_ratio", "tab_ratio",
    "prefix_increment_ratio", "avg_indent", "indent_consistency",
    "code_density", "statements_per_line", "multi_statement_ratio",
    "inline_if_ratio",
}

PROBLEM_DEPENDENT_FEATURES = {
    "total_lines", "total_tokens", "function_count", "has_helper_functions",
    "max_nesting_depth", "avg_nesting_depth", "lines_per_function",
    "if_density", "else_ratio", "ternary_usage", "likely_recursive",
    "global_variable_count", "uses_vector", "uses_map", "uses_set",
    "uses_pair", "uses_array", "uses_sort", "unique_token_ratio",
    "bigram_diversity",
}

STYLE_WEIGHT = 1.0
PROBLEM_WEIGHT = 0.3

MIN_PROFILE_SUBMISSIONS = 5


class AnomalyDetector:
    def __init__(self):
        self.extractor = FeatureExtractor()
        self.comparator = StyleComparator()

    def analyze_submission(
        self,
        source_code: str,
        user_profile: dict,
        profile_submission_count: int = 0,
        group_profiles: dict[str, dict] | None = None,
        ai_profile: dict | None = None,
    ) -> dict:
        features = self.extractor.extract(source_code)

        is_learning = profile_submission_count < MIN_PROFILE_SUBMISSIONS

        self_comparison = self.comparator.compare_to_profile(features, user_profile)
        anomaly_score = self._compute_anomaly_score(self_comparison, is_learning)

        if is_learning:
            verdict = "LEARNING"
            anomaly_score = min(anomaly_score, 0.3)
        else:
            verdict = self._determine_verdict(anomaly_score)

        result = {
            "anomaly_score": round(anomaly_score, 3),
            "features": features,
            "self_comparison": self_comparison,
            "verdict": verdict,
            "confidence": self._determine_confidence(self_comparison, is_learning),
            "top_deviations": self._get_top_deviations(self_comparison, n=10),
        }

        if ai_profile:
            ai_comparison = self.comparator.compare_to_profile(features, ai_profile)
            ai_similarity = 1.0 / (1.0 + ai_comparison["avg_deviation"])
            result["ai_score"] = round(ai_similarity, 3)
            result["ai_comparison"] = ai_comparison

        if group_profiles:
            cross_matches = self.comparator.cross_compare(features, group_profiles)
            result["cross_matches"] = cross_matches[:5]

        result["classification"] = self._classify(result)

        return result

    def _compute_anomaly_score(self, comparison: dict, is_learning: bool) -> float:
        deviations = comparison["feature_deviations"]
        if not deviations:
            return 0.0

        style_total = 0.0
        style_count = 0
        problem_total = 0.0
        problem_count = 0
        style_high = 0
        style_med = 0

        for key, dev in deviations.items():
            z = min(dev["z_score"], 10.0)
            if key in STYLE_FEATURES:
                style_total += z
                style_count += 1
                if dev["severity"] == "HIGH":
                    style_high += 1
                elif dev["severity"] == "MEDIUM":
                    style_med += 1
            elif key in PROBLEM_DEPENDENT_FEATURES:
                problem_total += z
                problem_count += 1

        style_avg = style_total / max(style_count, 1)
        problem_avg = problem_total / max(problem_count, 1)

        weighted_avg = (
            (style_avg * STYLE_WEIGHT + problem_avg * PROBLEM_WEIGHT)
            / (STYLE_WEIGHT + PROBLEM_WEIGHT)
        )

        score = min(1.0, (weighted_avg / 6.0) + (style_high * 0.04) + (style_med * 0.015))
        return score

    def _determine_verdict(self, anomaly_score: float) -> str:
        if anomaly_score < 0.4:
            return "AUTHENTIC"
        elif anomaly_score < 0.7:
            return "MINOR_DEVIATION"
        elif anomaly_score < 0.85:
            return "SIGNIFICANT_DEVIATION"
        else:
            return "ANOMALOUS"

    def _determine_confidence(self, comparison: dict, is_learning: bool) -> str:
        if is_learning:
            return "LOW"
        high_count = comparison["high_deviation_count"]
        if high_count >= 10:
            return "HIGH"
        elif high_count >= 5:
            return "MEDIUM"
        else:
            return "LOW"

    def _get_top_deviations(self, comparison: dict, n: int = 10) -> list[dict]:
        deviations = comparison["feature_deviations"]
        sorted_devs = sorted(
            deviations.items(),
            key=lambda x: x[1]["z_score"],
            reverse=True,
        )
        return [
            {"feature": name, **data}
            for name, data in sorted_devs[:n]
        ]

    def _classify(self, result: dict) -> str:
        if result["verdict"] == "LEARNING":
            return "LEARNING"

        anomaly = result["anomaly_score"]
        ai_score = result.get("ai_score", 0.0)

        if anomaly < 0.4:
            return "AUTHENTIC"

        if ai_score > 0.7 and anomaly > 0.6:
            return "LIKELY_AI"

        cross = result.get("cross_matches", [])
        if cross and cross[0]["similarity"] > 0.8 and anomaly > 0.6:
            return "LIKELY_OTHER_STUDENT"

        if anomaly > 0.7:
            return "ANOMALOUS_UNKNOWN"

        return "MINOR_DEVIATION"
