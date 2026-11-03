//! Shallow Python symbol/import extraction (regex). AST depth stays in Python.

use regex::Regex;
use std::sync::OnceLock;

use super::{Relation, Symbol};

fn class_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| Regex::new(r"(?m)^[ \t]*class\s+([A-Za-z_][\w]*)\s*[:(]").unwrap())
}

fn def_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| {
        Regex::new(r"(?m)^[ \t]*(?:async\s+)?def\s+([A-Za-z_][\w]*)\s*\(").unwrap()
    })
}

fn import_from_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| {
        Regex::new(r"(?m)^from\s+([A-Za-z_][\w.]*)\s+import\s+([A-Za-z_*(][\w\s,*()]*)").unwrap()
    })
}

fn import_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| Regex::new(r"(?m)^import\s+([A-Za-z_][\w.]*(?:\s*,\s*[A-Za-z_][\w.]*)*)").unwrap())
}

fn line_at(source: &str, start: usize) -> usize {
    source[..start].bytes().filter(|b| *b == b'\n').count() + 1
}

pub fn parse_symbols(source: &str, rel_path: &str) -> Vec<Symbol> {
    let mut out = Vec::new();
    for caps in class_re().captures_iter(source) {
        let line = line_at(source, caps.get(0).unwrap().start());
        out.push(Symbol {
            name: caps.get(1).unwrap().as_str().to_string(),
            kind: "class".into(),
            file_path: rel_path.to_string(),
            start_line: line,
            end_line: line,
        });
    }
    for caps in def_re().captures_iter(source) {
        let line = line_at(source, caps.get(0).unwrap().start());
        out.push(Symbol {
            name: caps.get(1).unwrap().as_str().to_string(),
            kind: "function".into(),
            file_path: rel_path.to_string(),
            start_line: line,
            end_line: line,
        });
    }
    out
}

pub fn parse_imports(source: &str, rel_path: &str) -> Vec<Relation> {
    let mut edges = Vec::new();
    let mut seen = std::collections::HashSet::new();
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_auth_service() {
        let src = "class AuthService:\n    def login(self, u: str) -> bool:\n        return True\n";
        let syms = parse_symbols(src, "auth.py");
        assert!(syms.iter().any(|s| s.name == "AuthService"));
        assert!(syms.iter().any(|s| s.name == "login"));
    }
}
