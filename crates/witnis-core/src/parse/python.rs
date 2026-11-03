//! Deeper shallow Python extraction (line/indent aware). Full AST depth stays in Python.

use regex::Regex;
use std::collections::{HashMap, HashSet};
use std::sync::OnceLock;

use super::{Relation, Symbol};

fn class_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| Regex::new(r"^[ \t]*class\s+([A-Za-z_][\w]*)\s*([:(])").unwrap())
}

fn class_bases_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| Regex::new(r"^[ \t]*class\s+([A-Za-z_][\w]*)\s*\(([^)]*)\)").unwrap())
}

fn def_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| {
        Regex::new(r"^[ \t]*(?:async\s+)?def\s+([A-Za-z_][\w]*)\s*\(").unwrap()
    })
}

fn decorator_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| Regex::new(r"^[ \t]*@([A-Za-z_][\w.]*)").unwrap())
}

fn import_from_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| {
        Regex::new(r"(?m)^from\s+([A-Za-z_][\w.]*)\s+import\s+([A-Za-z_*(][\w\s,*()]*)").unwrap()
    })
}

fn import_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| {
        Regex::new(r"(?m)^import\s+([A-Za-z_][\w.]*(?:\s*,\s*[A-Za-z_][\w.]*)*)").unwrap()
    })
}

fn call_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| Regex::new(r"\b([A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)*)\s*\(").unwrap())
}

const CALL_SKIP: &[&str] = &[
    "bool", "int", "str", "float", "list", "dict", "set", "tuple", "len", "print", "range",
    "type", "isinstance", "getattr", "setattr", "super", "property", "classmethod",
    "staticmethod", "if", "for", "while", "with", "return", "yield", "await", "assert",
    "raise", "except", "class", "def", "async", "lambda", "not", "and", "or", "in", "is",
];

fn leading_ws(line: &str) -> usize {
    line.chars().take_while(|c| *c == ' ' || *c == '\t').count()
}

fn line_at(source: &str, start: usize) -> usize {
    source[..start].bytes().filter(|b| *b == b'\n').count() + 1
}

pub fn parse_symbols(source: &str, rel_path: &str) -> Vec<Symbol> {
    let mut out = Vec::new();
    let mut current_class: Option<(String, usize)> = None;

    for (idx, line) in source.lines().enumerate() {
        let line_no = idx + 1;
        let trimmed = line.trim_start();
        if trimmed.is_empty() || trimmed.starts_with('#') || trimmed.starts_with('@') {
            continue;
        }
        let indent = leading_ws(line);

        if let Some((_, cindent)) = &current_class {
            if indent <= *cindent {
                current_class = None;
            }
        }

        if let Some(caps) = class_re().captures(line) {
            let name = caps.get(1).unwrap().as_str().to_string();
            current_class = Some((name.clone(), indent));
            out.push(Symbol {
                name,
                kind: "class".into(),
                file_path: rel_path.to_string(),
                start_line: line_no,
                end_line: line_no,
            });
            continue;
        }

        if let Some(caps) = def_re().captures(line) {
            let name = caps.get(1).unwrap().as_str().to_string();
            if let Some((cls, cindent)) = &current_class {
                if indent > *cindent {
                    out.push(Symbol {
                        name: format!("{cls}.{name}"),
                        kind: "method".into(),
                        file_path: rel_path.to_string(),
                        start_line: line_no,
                        end_line: line_no,
                    });
                    continue;
                }
            }
            out.push(Symbol {
                name,
                kind: "function".into(),
                file_path: rel_path.to_string(),
                start_line: line_no,
                end_line: line_no,
            });
        }
    }
    out
}

pub fn parse_imports(source: &str, rel_path: &str) -> Vec<Relation> {
    let mut edges = Vec::new();
    let mut seen = HashSet::new();
    for caps in import_from_re().captures_iter(source) {
        let module = caps.get(1).unwrap().as_str();
        let names = caps.get(2).unwrap().as_str();
        let line = line_at(source, caps.get(0).unwrap().start());
        for part in names.split(',') {
            let name = part.trim().split_whitespace().next().unwrap_or("").trim();
            if name.is_empty() || name == "(" || name == ")" {
                continue;
            }
            let name = name.trim_matches(|c| c == '(' || c == ')' || c == '*');
            if name.is_empty() {
                continue;
            }
            let target = format!("{module}.{name}");
            if seen.insert((target.clone(), line)) {
                edges.push(Relation {
                    source: rel_path.to_string(),
                    target,
                    relation_type: "imports_from".into(),
                    status: "observed".into(),
                    start_line: Some(line),
                });
            }
        }
    }
    for caps in import_re().captures_iter(source) {
        let line = line_at(source, caps.get(0).unwrap().start());
        for part in caps.get(1).unwrap().as_str().split(',') {
            let target = part.trim().to_string();
            if target.is_empty() {
                continue;
            }
            if seen.insert((target.clone(), line)) {
                edges.push(Relation {
                    source: rel_path.to_string(),
                    target,
                    relation_type: "imports".into(),
                    status: "observed".into(),
                    start_line: Some(line),
                });
            }
        }
    }
    edges
}

pub fn parse_inheritance(source: &str, rel_path: &str) -> Vec<Relation> {
    let mut edges = Vec::new();
    for (idx, line) in source.lines().enumerate() {
        let Some(caps) = class_bases_re().captures(line) else {
            continue;
        };
        let cls = caps.get(1).unwrap().as_str();
        let bases = caps.get(2).unwrap().as_str();
        let line_no = idx + 1;
        for part in bases.split(',') {
            let base = part.trim().split_whitespace().next().unwrap_or("").trim();
            if base.is_empty() || base == "object" {
                continue;
            }
            // Skip keyword-only / metaclass forms like metaclass=
            if base.contains('=') {
                continue;
            }
            edges.push(Relation {
                source: format!("{rel_path}:{cls}"),
                target: base.to_string(),
                relation_type: "inherits".into(),
                status: "observed".into(),
                start_line: Some(line_no),
            });
        }
    }
    edges
}

pub fn parse_decorators(source: &str, rel_path: &str) -> Vec<Relation> {
    let mut edges = Vec::new();
    let mut pending: Vec<(String, usize)> = Vec::new();
    let mut current_class: Option<(String, usize)> = None;

    for (idx, line) in source.lines().enumerate() {
        let line_no = idx + 1;
        let trimmed = line.trim_start();
        if trimmed.is_empty() || trimmed.starts_with('#') {
            continue;
        }
        let indent = leading_ws(line);

        if let Some(caps) = decorator_re().captures(line) {
            pending.push((caps.get(1).unwrap().as_str().to_string(), line_no));
            continue;
        }

        if let Some((_, cindent)) = &current_class {
            if indent <= *cindent && !trimmed.starts_with('@') {
                // leaving class when a peer/top-level statement appears
                if class_re().is_match(line) || (def_re().is_match(line) && indent <= *cindent) {
                    if indent <= *cindent {
                        current_class = None;
                    }
                }
            }
        }

        if let Some(caps) = class_re().captures(line) {
            let name = caps.get(1).unwrap().as_str().to_string();
            for (dec, dline) in pending.drain(..) {
                edges.push(Relation {
                    source: format!("{rel_path}:{name}"),
                    target: dec,
                    relation_type: "decorated_by".into(),
                    status: "observed".into(),
                    start_line: Some(dline),
                });
            }
            current_class = Some((name, indent));
            continue;
        }

        if let Some(caps) = def_re().captures(line) {
            let name = caps.get(1).unwrap().as_str().to_string();
            let owner = if let Some((cls, cindent)) = &current_class {
                if indent > *cindent {
                    format!("{cls}.{name}")
                } else {
                    name
                }
            } else {
                name
            };
            for (dec, dline) in pending.drain(..) {
                edges.push(Relation {
                    source: format!("{rel_path}:{owner}"),
                    target: dec,
                    relation_type: "decorated_by".into(),
                    status: "observed".into(),
                    start_line: Some(dline),
                });
            }
            continue;
        }

        pending.clear();
    }
    edges
}

pub fn parse_overrides(source: &str, rel_path: &str) -> Vec<Relation> {
    let symbols = parse_symbols(source, rel_path);
    let inherits = parse_inheritance(source, rel_path);

    let mut class_methods: HashMap<String, Vec<(String, usize)>> = HashMap::new();
    for s in &symbols {
        if s.kind != "method" {
            continue;
        }
        if let Some((cls, method)) = s.name.split_once('.') {
            class_methods
                .entry(cls.to_string())
                .or_default()
                .push((method.to_string(), s.start_line));
        }
    }

    let mut class_bases: HashMap<String, Vec<String>> = HashMap::new();
    for edge in &inherits {
        let cls = edge.source.rsplit(':').next().unwrap_or("").to_string();
        let base = edge.target.split('.').next_back().unwrap_or(&edge.target).to_string();
        class_bases.entry(cls).or_default().push(base);
    }

    let mut edges = Vec::new();
    for (cls, methods) in &class_methods {
        for base in class_bases.get(cls).into_iter().flatten() {
            let base_methods: Option<HashSet<&str>> = class_methods.get(base).map(|ms| {
                ms.iter().map(|(m, _)| m.as_str()).collect()
            });
            for (method, line) in methods {
                if let Some(ref bm) = base_methods {
                    if !bm.contains(method.as_str()) {
                        continue;
                    }
                    edges.push(Relation {
                        source: format!("{rel_path}:{cls}.{method}"),
                        target: format!("{base}.{method}"),
                        relation_type: "overrides".into(),
                        status: "observed".into(),
                        start_line: Some(*line),
                    });
                } else if !method.starts_with("__") {
                    edges.push(Relation {
                        source: format!("{rel_path}:{cls}.{method}"),
                        target: format!("{base}.{method}"),
                        relation_type: "overrides".into(),
                        status: "derived".into(),
                        start_line: Some(*line),
                    });
                }
            }
        }
    }
    edges
}

pub fn parse_calls(source: &str, rel_path: &str) -> Vec<Relation> {
    let mut edges = Vec::new();
    let mut seen = HashSet::new();
    let skip: HashSet<&str> = CALL_SKIP.iter().copied().collect();

    // Determine enclosing owner per line (best-effort).
    let mut owners: Vec<String> = Vec::new();
    let mut current_class: Option<(String, usize)> = None;
    let mut current_fn: Option<(String, usize)> = None;

    for line in source.lines() {
        let trimmed = line.trim_start();
        let indent = leading_ws(line);
        if !trimmed.is_empty() && !trimmed.starts_with('#') && !trimmed.starts_with('@') {
            if let Some((_, cindent)) = &current_class {
                if indent <= *cindent {
                    current_class = None;
                    current_fn = None;
                }
            }
            if let Some((_, findent)) = &current_fn {
                if indent <= *findent {
                    current_fn = None;
                }
            }
            if let Some(caps) = class_re().captures(line) {
                current_class = Some((caps.get(1).unwrap().as_str().to_string(), indent));
                current_fn = None;
            } else if let Some(caps) = def_re().captures(line) {
                let name = caps.get(1).unwrap().as_str().to_string();
                let owner = if let Some((cls, cindent)) = &current_class {
                    if indent > *cindent {
                        format!("{cls}.{name}")
                    } else {
                        name
                    }
                } else {
                    name
                };
                current_fn = Some((owner, indent));
            }
        }
        let owner = current_fn
            .as_ref()
            .map(|(o, _)| format!("{rel_path}:{o}"))
            .unwrap_or_else(|| rel_path.to_string());
        owners.push(owner);
    }

    for (idx, line) in source.lines().enumerate() {
        let trimmed = line.trim_start();
        if trimmed.is_empty() || trimmed.starts_with('#') {
            continue;
        }
        if class_re().is_match(line) || def_re().is_match(line) || decorator_re().is_match(line) {
            continue;
        }
        let owner = owners.get(idx).cloned().unwrap_or_else(|| rel_path.to_string());
        for caps in call_re().captures_iter(trimmed) {
            let target = caps.get(1).unwrap().as_str();
            let head = target.split('.').next().unwrap_or(target);
            if skip.contains(head) || skip.contains(target) {
                continue;
            }
            let line_no = idx + 1;
            if seen.insert((owner.clone(), target.to_string(), line_no)) {
                edges.push(Relation {
                    source: owner.clone(),
                    target: target.to_string(),
                    relation_type: "calls".into(),
                    status: "observed".into(),
                    start_line: Some(line_no),
                });
            }
        }
    }
    edges
}

/// All shallow Python relations for indexing.
pub fn parse_relations(source: &str, rel_path: &str) -> Vec<Relation> {
    let mut edges = parse_imports(source, rel_path);
    edges.extend(parse_inheritance(source, rel_path));
    edges.extend(parse_decorators(source, rel_path));
    edges.extend(parse_overrides(source, rel_path));
    edges.extend(parse_calls(source, rel_path));
    edges
}

#[cfg(test)]
mod tests {
    use super::*;

    const AUTH: &str = r#"
def audit(fn):
    return fn

class AuthService:
    @audit
    def login(self, username: str, password: str) -> bool:
        return bool(username and password)

def public_helper() -> str:
    return "ok"

class SecureAuth(AuthService):
    def login(self, username: str, password: str) -> bool:
        return super().login(username, password) and username != "banned"
"#;

    #[test]
    fn parses_methods_qualified() {
        let syms = parse_symbols(AUTH, "auth.py");
        assert!(syms.iter().any(|s| s.name == "AuthService" && s.kind == "class"));
        assert!(syms
            .iter()
            .any(|s| s.name == "AuthService.login" && s.kind == "method"));
        assert!(syms
            .iter()
            .any(|s| s.name == "public_helper" && s.kind == "function"));
        assert!(syms
            .iter()
            .any(|s| s.name == "SecureAuth.login" && s.kind == "method"));
    }

    #[test]
    fn parses_inheritance_and_overrides() {
        let edges = parse_relations(AUTH, "auth.py");
        assert!(edges.iter().any(|e| {
            e.relation_type == "inherits" && e.source == "auth.py:SecureAuth" && e.target == "AuthService"
        }));
        assert!(edges.iter().any(|e| {
            e.relation_type == "overrides"
                && e.source == "auth.py:SecureAuth.login"
                && e.target == "AuthService.login"
        }));
        assert!(edges.iter().any(|e| {
            e.relation_type == "decorated_by"
                && e.source == "auth.py:AuthService.login"
                && e.target == "audit"
        }));
    }
}
