import re
from difflib import SequenceMatcher

import numpy as np


def normalize_code(code: str) -> str:
    code = re.sub(r'//.*', '', code)
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    code = re.sub(r'\s+', ' ', code).strip()
    return code


def tokenize_code(code: str) -> list[str]:
    return re.findall(r'[a-zA-Z_]\w*|[^\s\w]', code)


def code_similarity(code_a: str, code_b: str) -> float:
    norm_a = normalize_code(code_a)
    norm_b = normalize_code(code_b)

    if not norm_a or not norm_b:
        return 0.0

    tokens_a = tokenize_code(norm_a)
    tokens_b = tokenize_code(norm_b)

    if not tokens_a or not tokens_b:
        return 0.0

    set_a = set(tokens_a)
    set_b = set(tokens_b)
    jaccard = len(set_a & set_b) / len(set_a | set_b) if (set_a | set_b) else 0.0

    seq_sim = SequenceMatcher(None, tokens_a, tokens_b).ratio()

    return round(0.4 * jaccard + 0.6 * seq_sim, 3)


class StyleComparator:
    def compare_to_profile(self, features: dict, profile: dict) -> dict:
        deviations = {}
        total_deviation = 0.0
        feature_count = 0

        for key, value in features.items():
            if key not in profile:
                continue

            prof = profile[key]
            mean = prof["mean"]
            std = prof["std"]

            if std == 0:
                if value == mean:
                    z_score = 0.0
                else:
                    z_score = 10.0  # never seen this variation
            else:
                z_score = abs(value - mean) / std

            severity = self._z_to_severity(z_score)
            deviations[key] = {
                "value": value,
                "expected_mean": mean,
                "expected_std": std,
                "z_score": round(z_score, 2),
                "severity": severity,
            }
            total_deviation += min(z_score, 10.0)
            feature_count += 1

        avg_deviation = total_deviation / max(feature_count, 1)

        return {
            "feature_deviations": deviations,
            "avg_deviation": round(avg_deviation, 3),
            "max_deviation": round(max((d["z_score"] for d in deviations.values()), default=0), 2),
            "high_deviation_count": sum(1 for d in deviations.values() if d["severity"] == "HIGH"),
            "medium_deviation_count": sum(1 for d in deviations.values() if d["severity"] == "MEDIUM"),
        }

    def compare_profiles(self, profile_a: dict, profile_b: dict) -> float:
        common_keys = set(profile_a.keys()) & set(profile_b.keys())
        if not common_keys:
            return 0.0

        vec_a = np.array([profile_a[k]["mean"] for k in common_keys])
        vec_b = np.array([profile_b[k]["mean"] for k in common_keys])

        # normalize
        norms_a = np.linalg.norm(vec_a)
        norms_b = np.linalg.norm(vec_b)

        if norms_a == 0 or norms_b == 0:
            return 0.0

        cosine_sim = np.dot(vec_a, vec_b) / (norms_a * norms_b)
        return float(max(0.0, cosine_sim))

    def cross_compare(self, features: dict, all_profiles: dict[str, dict]) -> list[dict]:
        results = []
        for student_id, profile in all_profiles.items():
            comparison = self.compare_to_profile(features, profile)
            similarity = 1.0 / (1.0 + comparison["avg_deviation"])
            results.append({
                "student_id": student_id,
                "similarity": round(similarity, 3),
                "avg_deviation": comparison["avg_deviation"],
            })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results

    def _z_to_severity(self, z_score: float) -> str:
        if z_score < 1.5:
            return "LOW"
        elif z_score < 3.0:
            return "MEDIUM"
        else:
            return "HIGH"
