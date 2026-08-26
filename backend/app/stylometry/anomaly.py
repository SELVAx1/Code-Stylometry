from app.stylometry.extractor import FeatureExtractor
from app.stylometry.comparator import StyleComparator


class AnomalyDetector:
    def __init__(self):
        self.extractor = FeatureExtractor()
        self.comparator = StyleComparator()

    def analyze_submission(
        self,
        source_code: str,
        user_profile: dict,
        group_profiles: dict[str, dict] | None = None,
        ai_profile: dict | None = None,
    ) -> dict:
        features = self.extractor.extract(source_code)

        # Compare against user's own profile
        self_comparison = self.comparator.compare_to_profile(features, user_profile)
        anomaly_score = self._compute_anomaly_score(self_comparison)

        result = {
            "anomaly_score": round(anomaly_score, 3),
            "features": features,
            "self_comparison": self_comparison,
            "verdict": self._determine_verdict(anomaly_score),
            "confidence": self._determine_confidence(self_comparison),
            "top_deviations": self._get_top_deviations(self_comparison, n=10),
        }

        # Compare against AI profile if available
        if ai_profile:
            ai_comparison = self.comparator.compare_to_profile(features, ai_profile)
            ai_similarity = 1.0 / (1.0 + ai_comparison["avg_deviation"])
            result["ai_score"] = round(ai_similarity, 3)
            result["ai_comparison"] = ai_comparison

        # Cross-compare against group if available
        if group_profiles:
            cross_matches = self.comparator.cross_compare(features, group_profiles)
            result["cross_matches"] = cross_matches[:5]  # top 5 matches

        # Final classification
        result["classification"] = self._classify(result)

        return result

    def _compute_anomaly_score(self, comparison: dict) -> float:
        avg_dev = comparison["avg_deviation"]
        high_count = comparison["high_deviation_count"]
        med_count = comparison["medium_deviation_count"]

        # weighted score: average deviation + penalty for high-deviation features
        score = min(1.0, (avg_dev / 5.0) + (high_count * 0.05) + (med_count * 0.02))
        return score

    def _determine_verdict(self, anomaly_score: float) -> str:
        if anomaly_score < 0.3:
            return "AUTHENTIC"
        elif anomaly_score < 0.6:
            return "MINOR_DEVIATION"
        elif anomaly_score < 0.8:
            return "SIGNIFICANT_DEVIATION"
        else:
            return "ANOMALOUS"

    def _determine_confidence(self, comparison: dict) -> str:
        high_count = comparison["high_deviation_count"]
        if high_count >= 8:
            return "HIGH"
        elif high_count >= 4:
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
        anomaly = result["anomaly_score"]
        ai_score = result.get("ai_score", 0.0)

        if anomaly < 0.3:
            return "AUTHENTIC"

        if ai_score > 0.7 and anomaly > 0.5:
            return "LIKELY_AI"

        cross = result.get("cross_matches", [])
        if cross and cross[0]["similarity"] > 0.8 and anomaly > 0.5:
            return "LIKELY_OTHER_STUDENT"

        if anomaly > 0.6:
            return "ANOMALOUS_UNKNOWN"

        return "MINOR_DEVIATION"
