import numpy as np


class ProfileBuilder:
    def build_profile(self, feature_vectors: list[dict]) -> dict:
        if not feature_vectors:
            return {}

        all_keys = set()
        for fv in feature_vectors:
            all_keys.update(fv.keys())

        profile = {}
        for key in sorted(all_keys):
            values = [fv.get(key, 0.0) for fv in feature_vectors]
            values = [v for v in values if v is not None]

            if not values:
                continue

            arr = np.array(values, dtype=float)
            profile[key] = {
                "mean": float(np.mean(arr)),
                "std": float(np.std(arr)),
                "min": float(np.min(arr)),
                "max": float(np.max(arr)),
                "median": float(np.median(arr)),
                "consistency": self._compute_consistency(arr),
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
                # running update of mean and std
                n = old.get("count", 10)
                old_mean = old["mean"]
                new_mean = (old_mean * n + new_val) / (n + 1)
                old_std = old["std"]
                new_std = np.sqrt((n * (old_std**2 + (old_mean - new_mean)**2) + (new_val - new_mean)**2) / (n + 1))
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
