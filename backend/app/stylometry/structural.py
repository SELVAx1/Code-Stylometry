import re


def extract_structural_features(source_code: str) -> dict:
    features = {}
    lines = source_code.split("\n")

    # Function count
    func_pattern = r'(?:int|void|long\s+long|double|bool|string|auto|vector|pair)\s+\w+\s*\([^)]*\)\s*\{'
    functions = re.findall(func_pattern, source_code)
    features["function_count"] = len(functions)
    features["has_helper_functions"] = 1.0 if len(functions) > 1 else 0.0

    # Nesting depth
    max_depth = 0
    current_depth = 0
    for char in source_code:
        if char == '{':
            current_depth += 1
            max_depth = max(max_depth, current_depth)
        elif char == '}':
            current_depth = max(0, current_depth - 1)
    features["max_nesting_depth"] = max_depth
    features["avg_nesting_depth"] = _compute_avg_nesting(source_code)

    # Code structure
    features["lines_per_function"] = len(lines) / max(len(functions), 1)

    # Control flow density
    if_count = len(re.findall(r'\bif\s*\(', source_code))
    else_count = len(re.findall(r'\belse\b', source_code))
    ternary_count = source_code.count('?')
    features["if_density"] = if_count / max(len(lines), 1)
    features["else_ratio"] = else_count / max(if_count, 1)
    features["ternary_usage"] = ternary_count / max(len(lines), 1)

    # Recursion indicator
    features["likely_recursive"] = 1.0 if _detect_recursion(source_code) else 0.0

    # Global variables
    global_vars = _count_globals(source_code)
    features["global_variable_count"] = global_vars

    # Code density (non-blank, non-comment lines / total lines)
    code_lines = [l for l in lines if l.strip() and not l.strip().startswith("//")]
    features["code_density"] = len(code_lines) / max(len(lines), 1)

    # Statement density (semicolons per line)
    features["statements_per_line"] = source_code.count(';') / max(len(lines), 1)

    # Multi-statement lines
    multi_statement = sum(1 for l in lines if l.count(';') > 1)
    features["multi_statement_ratio"] = multi_statement / max(len(lines), 1)

    # Inline conditionals (single-line if)
    inline_if = len(re.findall(r'if\s*\([^)]+\)\s*\w', source_code))
    features["inline_if_ratio"] = inline_if / max(if_count, 1)

    return features


def _compute_avg_nesting(source_code: str) -> float:
    depth = 0
    total_depth = 0
    line_count = 0
    for line in source_code.split("\n"):
        if '{' in line:
            depth += line.count('{')
        if line.strip():
            total_depth += depth
            line_count += 1
        if '}' in line:
            depth -= line.count('}')
            depth = max(0, depth)
    return total_depth / max(line_count, 1)


def _detect_recursion(source_code: str) -> bool:
    func_names = re.findall(r'(?:int|void|long\s+long|double|bool|string)\s+(\w+)\s*\(', source_code)
    for name in func_names:
        pattern = rf'\b{name}\s*\('
        occurrences = re.findall(pattern, source_code)
        if len(occurrences) > 1:
            return True
    return False


def _count_globals(source_code: str) -> int:
    lines = source_code.split("\n")
    depth = 0
    global_count = 0
    for line in lines:
        depth += line.count('{') - line.count('}')
        if depth == 0 and re.match(r'\s*(int|long|double|char|bool|string|vector|map|set)\s+\w+', line):
            if not line.strip().startswith("#") and "(" not in line:
                global_count += 1
    return global_count
