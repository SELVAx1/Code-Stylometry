import numpy as np


class ProfileBuilder:
    def build_profile(self, feature_vectors: list[dict]) -> dict:
        if not feature_vectors:
            return {}

        all_keys = set()
        for fv in feature_vectors:
            all_keys.update(fv.keys())

        n = len(feature_vectors)
        weights = np.array([
            1.0 + (i / max(n - 1, 1))
            for i in range(n)
        ])
        weights = weights / weights.sum()

        profile = {}
        for key in sorted(all_keys):
            values = []
            w_list = []
            for i, fv in enumerate(feature_vectors):
                v = fv.get(key, None)
                if v is not None:
                    values.append(v)
                    w_list.append(weights[i])

            if not values:
                continue

            arr = np.array(values, dtype=float)
            w = np.array(w_list, dtype=float)
            w = w / w.sum()

            wmean = float(np.average(arr, weights=w))
            wvar = float(np.average((arr - wmean) ** 2, weights=w))
            wstd = float(np.sqrt(wvar))

            profile[key] = {
                "mean": wmean,
                "std": wstd,
                "min": float(np.min(arr)),
                "max": float(np.max(arr)),
                "median": float(np.median(arr)),
                "consistency": self._compute_consistency(arr),
                "count": len(values),
            }

        return profile

    def _compute_consistency(self, values: np.ndarray) -> float:
        if len(values) < 2:
            return 1.0
        std = np.std(values)
        mean = np.mean(values)
        if mean == 0:
            return 1.0 if std == 0 else 0.0
        cv = std / abs(mean)
        return max(0.0, 1.0 - cv)

    def update_profile(self, existing_profile: dict, new_features: dict) -> dict:
        if not existing_profile:
            return self.build_profile([new_features])

        updated = {}
        all_keys = set(existing_profile.keys()) | set(new_features.keys())

        for key in all_keys:
            if key in existing_profile and key in new_features:
                old = existing_profile[key]
                new_val = new_features[key]
                n = old.get("count", 10)
                decay = 0.95
                eff_n = n * decay
                old_mean = old["mean"]
                new_mean = (old_mean * eff_n + new_val) / (eff_n + 1)
                old_std = old["std"]
                new_std = np.sqrt(
                    (eff_n * (old_std**2 + (old_mean - new_mean)**2) + (new_val - new_mean)**2)
                    / (eff_n + 1)
                )
                updated[key] = {
                    "mean": float(new_mean),
                    "std": float(new_std),
                    "min": min(old.get("min", new_val), new_val),
                    "max": max(old.get("max", new_val), new_val),
                    "median": old.get("median", new_mean),
                    "consistency": old.get("consistency", 0.5),
                    "count": n + 1,
                }
            elif key in existing_profile:
                updated[key] = existing_profile[key]
            else:
                updated[key] = {
                    "mean": float(new_features[key]),
                    "std": 0.0,
                    "min": float(new_features[key]),
                    "max": float(new_features[key]),
                    "median": float(new_features[key]),
                    "consistency": 1.0,
                    "count": 1,
                }

        return updated
