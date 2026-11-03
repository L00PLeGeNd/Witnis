use regex::Regex;
use std::sync::OnceLock;

use super::{Relation, Symbol};

fn class_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| {
        Regex::new(r"(?m)^\s*(?:public\s+|protected\s+|private\s+)?(?:abstract\s+|final\s+)?class\s+([A-Za-z_][\w]*)")
            .unwrap()
    })
}

fn interface_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| {
        Regex::new(r"(?m)^\s*(?:public\s+|protected\s+|private\s+)?interface\s+([A-Za-z_][\w]*)")
            .unwrap()
    })
}

fn method_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| {
        Regex::new(r"(?m)^\s*(?:public|protected|private|static|\s)+[\w<>\[\]]+\s+([A-Za-z_][\w]*)\s*\(")
            .unwrap()
    })
}

fn import_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| Regex::new(r"(?m)^import\s+(?:static\s+)?([A-Za-z_][\w.]*)\s*;").unwrap())
}

fn extends_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| {
        Regex::new(r"(?m)class\s+([A-Za-z_][\w]*)\s+extends\s+([A-Za-z_][\w.]*)").unwrap()
    })
}

fn implements_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| {
        Regex::new(r"(?m)class\s+([A-Za-z_][\w]*)\b[^{;]*?\bimplements\s+([^{]+)\{").unwrap()
    })
}

fn call_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| Regex::new(r"\b([A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)*)\s*\(").unwrap())
}

const SKIP_METHODS: &[&str] = &["if", "for", "while", "switch", "catch", "return", "new", "class"];
const KEYWORDS: &[&str] = &[
    "if", "for", "while", "switch", "catch", "return", "new", "class", "super", "this", "System",
];

fn line_at(source: &str, start: usize) -> usize {
    source[..start].bytes().filter(|b| *b == b'\n').count() + 1
}

pub fn parse_symbols(source: &str, rel_path: &str) -> Vec<Symbol> {
    let mut out = Vec::new();
    for (re, kind) in [(class_re(), "class"), (interface_re(), "interface")] {
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
    for caps in method_re().captures_iter(source) {
        let name = caps.get(1).unwrap().as_str();
        if SKIP_METHODS.contains(&name) {
            continue;
        }
        let line = line_at(source, caps.get(0).unwrap().start());
        out.push(Symbol {
            name: name.to_string(),
            kind: "method".into(),
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
    for caps in import_re().captures_iter(source) {
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
    for caps in extends_re().captures_iter(source) {
        let line = line_at(source, caps.get(0).unwrap().start());
        edges.push(Relation {
            source: format!("{rel_path}:{}", caps.get(1).unwrap().as_str()),
            target: caps.get(2).unwrap().as_str().to_string(),
            relation_type: "inherits".into(),
            status: "observed".into(),
            start_line: Some(line),
        });
    }
    for caps in implements_re().captures_iter(source) {
        let line = line_at(source, caps.get(0).unwrap().start());
        let cls = caps.get(1).unwrap().as_str();
        for raw in caps.get(2).unwrap().as_str().split(',') {
            let iface = raw.trim().split('<').next().unwrap_or("").trim();
            let iface = iface.rsplit('.').next().unwrap_or(iface);
            if iface.is_empty() {
                continue;
            }
            edges.push(Relation {
                source: format!("{rel_path}:{cls}"),
                target: iface.to_string(),
                relation_type: "implements".into(),
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
        if KEYWORDS.contains(&leaf) || KEYWORDS.contains(&target) {
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
    fn parses_java_login() {
        let src = r#"
public class AuthService {
    public boolean login(String username, String password) { return true; }
}
"#;
        let syms = parse_symbols(src, "AuthService.java");
        assert!(syms.iter().any(|s| s.name == "AuthService" && s.kind == "class"));
        assert!(syms.iter().any(|s| s.name == "login"));
    }
}
