import re
from collections import Counter


def extract_lexical_features(source_code: str) -> dict:
    lines = source_code.split("\n")
    tokens = re.findall(r'\b\w+\b', source_code)

    features = {}

    # Line-level metrics
    line_lengths = [len(line) for line in lines if line.strip()]
    features["avg_line_length"] = sum(line_lengths) / max(len(line_lengths), 1)
    features["max_line_length"] = max(line_lengths) if line_lengths else 0
    features["total_lines"] = len(lines)
    features["blank_line_ratio"] = sum(1 for l in lines if not l.strip()) / max(len(lines), 1)

    # Include style
    features["uses_bits_stdc"] = 1.0 if "bits/stdc++.h" in source_code else 0.0
    features["uses_iostream"] = 1.0 if "#include <iostream>" in source_code or '#include<iostream>' in source_code else 0.0
    features["individual_includes"] = source_code.count("#include") - (1 if features["uses_bits_stdc"] else 0)

    # Brace style
    same_line_braces = len(re.findall(r'\)\s*\{', source_code))
    next_line_braces = len(re.findall(r'\)\s*\n\s*\{', source_code))
    total_braces = same_line_braces + next_line_braces
    features["brace_same_line_ratio"] = same_line_braces / max(total_braces, 1)

    # Spacing habits
    features["spaces_around_operators"] = len(re.findall(r'\w\s+[+\-*/=<>]+\s+\w', source_code)) / max(len(tokens), 1)
    features["space_after_comma"] = len(re.findall(r',\s', source_code)) / max(source_code.count(','), 1)
    features["space_before_paren"] = len(re.findall(r'\w\s+\(', source_code)) / max(source_code.count('('), 1)

    # Output style
    features["uses_endl"] = 1.0 if "endl" in source_code else 0.0
    features["uses_newline_char"] = 1.0 if r'"\n"' in source_code or r"'\\n'" in source_code else 0.0
    features["uses_printf"] = 1.0 if "printf" in source_code else 0.0
    features["uses_cout"] = 1.0 if "cout" in source_code else 0.0

    # Type preferences
    features["uses_long_long"] = 1.0 if "long long" in source_code else 0.0
    features["uses_int64"] = 1.0 if "int64_t" in source_code else 0.0
    features["uses_auto"] = source_code.count("auto") / max(len(tokens), 1)
    features["uses_typedef"] = 1.0 if "typedef" in source_code else 0.0
    features["uses_using_alias"] = 1.0 if re.search(r'using\s+\w+\s*=', source_code) else 0.0
    features["uses_define"] = source_code.count("#define") / max(len(lines), 1)

    # Loop style
    for_loops = len(re.findall(r'\bfor\s*\(', source_code))
    while_loops = len(re.findall(r'\bwhile\s*\(', source_code))
    range_for = len(re.findall(r'for\s*\(\s*auto', source_code))
    total_loops = for_loops + while_loops
    features["for_ratio"] = for_loops / max(total_loops, 1)
    features["while_ratio"] = while_loops / max(total_loops, 1)
    features["range_for_ratio"] = range_for / max(for_loops, 1)

    # Variable naming
    identifiers = re.findall(r'\b[a-zA-Z_]\w*\b', source_code)
    cpp_keywords = {
        "int", "long", "double", "float", "char", "bool", "void", "string",
        "vector", "map", "set", "pair", "queue", "stack", "auto", "const",
        "if", "else", "for", "while", "do", "return", "break", "continue",
        "class", "struct", "public", "private", "using", "namespace", "std",
        "include", "define", "true", "false", "nullptr", "sizeof", "typedef",
        "template", "typename", "static", "switch", "case", "default",
    }
    user_identifiers = [i for i in identifiers if i.lower() not in cpp_keywords and len(i) > 1]
    if user_identifiers:
        avg_id_len = sum(len(i) for i in user_identifiers) / len(user_identifiers)
        single_char = sum(1 for i in user_identifiers if len(i) == 1) / len(user_identifiers)
        has_underscore = sum(1 for i in user_identifiers if '_' in i) / len(user_identifiers)
        is_camel = sum(1 for i in user_identifiers if re.match(r'^[a-z]+[A-Z]', i)) / len(user_identifiers)
    else:
        avg_id_len = 0
        single_char = 0
        has_underscore = 0
        is_camel = 0

    features["avg_identifier_length"] = avg_id_len
    features["single_char_var_ratio"] = single_char
    features["underscore_naming_ratio"] = has_underscore
    features["camel_case_ratio"] = is_camel

    # Comment style
    single_comments = len(re.findall(r'//', source_code))
    multi_comments = len(re.findall(r'/\*', source_code))
    features["comment_density"] = (single_comments + multi_comments) / max(len(lines), 1)

    # STL usage
    features["uses_vector"] = 1.0 if "vector" in source_code else 0.0
    features["uses_map"] = 1.0 if re.search(r'\bmap\b', source_code) else 0.0
    features["uses_set"] = 1.0 if re.search(r'\bset\b', source_code) else 0.0
    features["uses_pair"] = 1.0 if "pair" in source_code else 0.0
    features["uses_array"] = 1.0 if re.search(r'\barray\b', source_code) else 0.0
    features["uses_sort"] = 1.0 if "sort(" in source_code else 0.0

    # Macro/template habits
    features["uses_pb"] = 1.0 if re.search(r'#define\s+pb\b', source_code) else 0.0
    features["uses_ll_macro"] = 1.0 if re.search(r'#define\s+ll\b', source_code) else 0.0
    features["has_template_header"] = 1.0 if source_code.strip().startswith("#include") and source_code.count("#define") >= 3 else 0.0

    # Input style
    features["uses_cin"] = 1.0 if "cin" in source_code else 0.0
    features["uses_scanf"] = 1.0 if "scanf" in source_code else 0.0
    features["uses_fast_io"] = 1.0 if "ios_base::sync_with_stdio" in source_code or "ios::sync_with_stdio" in source_code else 0.0

    # Return style
    features["has_return_0"] = 1.0 if "return 0" in source_code else 0.0

    # Keyword frequencies (normalized)
    keyword_freq = Counter(t for t in tokens if t in cpp_keywords)
    total_kw = sum(keyword_freq.values()) or 1
    for kw in ["if", "for", "while", "return", "int", "long", "auto", "const"]:
        features[f"kw_freq_{kw}"] = keyword_freq.get(kw, 0) / total_kw

    return features
