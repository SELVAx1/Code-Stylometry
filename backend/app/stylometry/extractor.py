from app.stylometry.lexical import extract_lexical_features
from app.stylometry.structural import extract_structural_features
from app.stylometry.statistical import extract_statistical_features


class FeatureExtractor:
    def extract(self, source_code: str) -> dict:
        features = {}
        features.update(extract_lexical_features(source_code))
        features.update(extract_structural_features(source_code))
        features.update(extract_statistical_features(source_code))
        return features

    def extract_batch(self, submissions: list[str]) -> list[dict]:
        return [self.extract(code) for code in submissions]
