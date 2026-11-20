use regex::Regex;
use std::sync::OnceLock;

use super::{Relation, Symbol};

fn func_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| Regex::new(r"(?m)^func\s+(?:\([^)]+\)\s+)?([A-Za-z_][\w]*)\s*\(").unwrap())
}

fn type_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| {
        Regex::new(r"(?m)^type\s+([A-Za-z_][\w]*)\s+(?:struct|interface|func|[A-Za-z_])").unwrap()
    })
}

fn import_block_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| Regex::new(r"(?ms)^import\s*\((.*?)\)").unwrap())
}

fn import_line_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| Regex::new(r#"(?m)^\s*(?:[A-Za-z_]\w*\s+)?"([^"]+)""#).unwrap())
}

fn import_single_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| Regex::new(r#"(?m)^import\s+(?:[A-Za-z_]\w*\s+)?"([^"]+)""#).unwrap())
}

fn call_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| Regex::new(r"\b([A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)*)\s*\(").unwrap())
}

const KEYWORDS: &[&str] = &[
    "if", "for", "switch", "select", "return", "go", "defer", "func", "type", "range", "make",
    "new", "append", "len", "cap", "close", "copy", "delete", "panic", "recover",
];

fn line_at(source: &str, start: usize) -> usize {
    source[..start].bytes().filter(|b| *b == b'\n').count() + 1
}

pub fn parse_symbols(source: &str, rel_path: &str) -> Vec<Symbol> {
    let mut out = Vec::new();
    for (re, kind) in [(type_re(), "type"), (func_re(), "function")] {
        for caps in re.captures_iter(source) {
            let line = line_at(source, caps.get(0).unwrap().start());
            out.push(Symbol {
                name: caps.get(1).unwrap().as_str().to_string(),
                kind: kind.to_string(),
                file_path: rel_path.to_string(),
                start_line: line,
                end_line: line,
            });
        }
    }
    out
}

pub fn parse_imports(source: &str, rel_path: &str) -> Vec<Relation> {
    let mut edges = Vec::new();
    let mut seen = std::collections::HashSet::new();
    for caps in import_block_re().captures_iter(source) {
        let block = caps.get(1).unwrap();
        let base = block.start();
        for im in import_line_re().captures_iter(block.as_str()) {
            let target = im.get(1).unwrap().as_str().to_string();
            let line = line_at(source, base + im.get(0).unwrap().start());
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
    for caps in import_single_re().captures_iter(source) {
        let target = caps.get(1).unwrap().as_str().to_string();
        let line = line_at(source, caps.get(0).unwrap().start());
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
    edges
}

pub fn parse_calls(source: &str, rel_path: &str) -> Vec<Relation> {
    let mut edges = Vec::new();
    let mut seen = std::collections::HashSet::new();
    for caps in call_re().captures_iter(source) {
        let target = caps.get(1).unwrap().as_str();
        let leaf = target.rsplit('.').next().unwrap_or(target);
        if KEYWORDS.contains(&leaf) {
            continue;
        }
        let line = line_at(source, caps.get(0).unwrap().start());
        if !seen.insert((target.to_string(), line)) {
            continue;
        }
        edges.push(Relation {
            source: format!("{rel_path}:module"),
            target: target.to_string(),
            relation_type: "calls".into(),
            status: "derived".into(),
            start_line: Some(line),
        });
    }
    edges
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_go_login() {
        let src = "package auth\ntype AuthService struct {}\nfunc (a *AuthService) Login(user string) bool { return true }\n";
        let syms = parse_symbols(src, "auth.go");
        assert!(syms.iter().any(|s| s.name == "AuthService"));
        assert!(syms.iter().any(|s| s.name == "Login"));
    }
}
