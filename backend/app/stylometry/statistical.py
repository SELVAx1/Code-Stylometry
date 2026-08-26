import re
from collections import Counter


def extract_statistical_features(source_code: str) -> dict:
    features = {}
    tokens = tokenize_cpp(source_code)

    # Token-level stats
    features["total_tokens"] = len(tokens)
    features["unique_token_ratio"] = len(set(tokens)) / max(len(tokens), 1)

    # Token bigrams
    bigrams = [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens) - 1)]
    bigram_counts = Counter(bigrams)
    top_bigrams = bigram_counts.most_common(20)

    # Bigram diversity
    features["bigram_diversity"] = len(set(bigrams)) / max(len(bigrams), 1)

    # Character-level features
    features["whitespace_ratio"] = source_code.count(' ') / max(len(source_code), 1)
    features["tab_ratio"] = source_code.count('\t') / max(len(source_code), 1)
    features["uses_tabs"] = 1.0 if '\t' in source_code else 0.0

    # Punctuation distribution
    punctuation = "{}()[];,.<>+-*/=&|!~^%?:"
    punct_counts = Counter(c for c in source_code if c in punctuation)
    total_punct = sum(punct_counts.values()) or 1
    for p, name in [("{", "open_brace"), ("}", "close_brace"), ("(", "open_paren"),
                     (";", "semicolon"), (",", "comma"), ("<", "angle_bracket")]:
        features[f"punct_{name}_ratio"] = punct_counts.get(p, 0) / total_punct

    # Operator preferences
    features["increment_style_prefix"] = len(re.findall(r'\+\+\w', source_code))
    features["increment_style_postfix"] = len(re.findall(r'\w\+\+', source_code))
    total_inc = features["increment_style_prefix"] + features["increment_style_postfix"]
    features["prefix_increment_ratio"] = features["increment_style_prefix"] / max(total_inc, 1)

    # Line ending patterns
    lines = source_code.split("\n")
    ends_with_semicolon = sum(1 for l in lines if l.rstrip().endswith(';'))
    ends_with_brace = sum(1 for l in lines if l.rstrip().endswith('{') or l.rstrip().endswith('}'))
    total_nonempty = sum(1 for l in lines if l.strip())
    features["semicolon_line_ratio"] = ends_with_semicolon / max(total_nonempty, 1)
    features["brace_line_ratio"] = ends_with_brace / max(total_nonempty, 1)

    # Indentation analysis
    indent_sizes = []
    for line in lines:
        if line and line[0] in (' ', '\t'):
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            indent_sizes.append(indent)
    if indent_sizes:
        features["avg_indent"] = sum(indent_sizes) / len(indent_sizes)
        features["indent_consistency"] = 1.0 - (len(set(indent_sizes)) / max(len(indent_sizes), 1))
    else:
        features["avg_indent"] = 0
        features["indent_consistency"] = 1.0

    return features


def tokenize_cpp(source_code: str) -> list[str]:
    token_pattern = r'[a-zA-Z_]\w*|[0-9]+|[+\-*/=<>!&|^~%]+|[{}()\[\];,.]|::|->|<<|>>'
    return re.findall(token_pattern, source_code)
