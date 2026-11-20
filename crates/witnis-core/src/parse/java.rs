use regex::Regex;
use std::collections::{HashMap, HashSet};
use std::path::Path;
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

fn class_header_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| {
        Regex::new(r"(?m)^\s*(?:public\s+|protected\s+|private\s+)?(?:abstract\s+|final\s+)?(class|interface)\s+([A-Za-z_][\w]*)")
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

fn method_header_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| {
        Regex::new(r"(?m)^\s*(?:public|protected|private|static|\s)+[\w<>\[\]]+\s+([A-Za-z_][\w]*)\s*\([^;]*\)\s*\{")
            .unwrap()
    })
}

fn method_sig_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| {
        Regex::new(
            r"(?m)^\s*(?:public|protected|private|static|final|synchronized|\s)+([A-Za-z_][\w.]*(?:<[^>\n]+>)?(?:\[\])?)\s+([A-Za-z_][\w]*)\s*\(([^)]*)\)\s*(?:throws\s+[^{]+)?\{",
        )
        .unwrap()
    })
}

fn field_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| {
        Regex::new(
            r"(?m)^\s*(?:public|protected|private|static|final|volatile|transient|\s)+([A-Za-z_][\w.]*(?:<[^;]+>)?)\s+([A-Za-z_][\w]*)\s*[;=]",
        )
        .unwrap()
    })
}

fn autowired_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| Regex::new(r"@Autowired\b|@Inject\b|@Resource\b").unwrap())
}

fn ctor_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| {
        Regex::new(r"(?m)^\s*(?:public|protected|private)\s+([A-Za-z_][\w]*)\s*\(([^)]*)\)\s*\{")
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
const USES_TYPE_SKIP: &[&str] = &[
    "if", "for", "while", "switch", "catch", "return", "new", "class", "super", "this", "System",
    "void", "int", "long", "boolean", "byte", "short", "char", "float", "double", "String",
    "Integer", "Long", "Boolean", "Object", "Class", "List", "Map", "Set", "Optional",
    "Collection", "Iterable", "Override", "Deprecated",
];

fn line_at(source: &str, start: usize) -> usize {
    source[..start].bytes().filter(|b| *b == b'\n').count() + 1
}

fn simple_type(type_expr: &str) -> String {
    let mut t = type_expr.trim();
    if let Some((head, _)) = t.split_once('<') {
        t = head.trim();
    }
    t = t.trim_end_matches(&['[', ']'][..]).trim();
    if let Some((_, tail)) = t.rsplit_once('.') {
        t = tail;
    }
    t.to_string()
}

fn enclosing_type(source: &str, pos: usize) -> Option<String> {
    let mut last: Option<String> = None;
    for caps in class_header_re().captures_iter(source) {
        let m = caps.get(0).unwrap();
        if m.start() > pos {
            break;
        }
        last = Some(caps.get(2).unwrap().as_str().to_string());
    }
    last
}

fn enclosing_method(source: &str, pos: usize) -> Option<String> {
    let mut best_pos: Option<usize> = None;
    let mut last: Option<String> = None;
    for caps in method_header_re().captures_iter(source) {
        let m = caps.get(0).unwrap();
        if m.start() > pos {
            break;
        }
        let name = caps.get(1).unwrap().as_str();
        if KEYWORDS.contains(&name) {
            continue;
        }
        if best_pos.map(|bp| m.start() >= bp).unwrap_or(true) {
            best_pos = Some(m.start());
            last = Some(name.to_string());
        }
    }
    for caps in ctor_re().captures_iter(source) {
        let m = caps.get(0).unwrap();
        if m.start() > pos {
            break;
        }
        if best_pos.map(|bp| m.start() >= bp).unwrap_or(true) {
            best_pos = Some(m.start());
            last = Some(caps.get(1).unwrap().as_str().to_string());
        }
    }
    last
}

fn extract_fields(source: &str) -> Vec<(String, String, usize, bool, usize)> {
    let mut out = Vec::new();
    for caps in field_re().captures_iter(source) {
        let m = caps.get(0).unwrap();
        let type_name = simple_type(caps.get(1).unwrap().as_str());
        let field = caps.get(2).unwrap().as_str().to_string();
        if KEYWORDS.contains(&type_name.as_str()) || KEYWORDS.contains(&field.as_str()) {
            continue;
        }
        let start = m.start();
        let win_start = start.saturating_sub(220);
        let window = &source[win_start..start];
        let injected = autowired_re().is_match(window);
        out.push((type_name, field, line_at(source, start), injected, start));
    }
    out
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
    let mut seen = HashSet::new();
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
            let iface = simple_type(raw);
            if iface.is_empty() || KEYWORDS.contains(&iface.as_str()) {
                continue;
            }
            edges.push(Relation {
                source: format!("{rel_path}:{cls}"),
                target: iface,
                relation_type: "implements".into(),
                status: "observed".into(),
                start_line: Some(line),
            });
        }
    }
    edges
}

pub fn parse_injections(source: &str, rel_path: &str) -> Vec<Relation> {
    let mut edges = Vec::new();
    let stem = Path::new(rel_path)
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or("module");

    for (type_name, _field, line, injected, pos) in extract_fields(source) {
        if !injected {
            continue;
        }
        let owner = enclosing_type(source, pos).unwrap_or_else(|| stem.to_string());
        edges.push(Relation {
            source: format!("{rel_path}:{owner}"),
            target: type_name,
            relation_type: "injects".into(),
            status: "derived".into(),
            start_line: Some(line),
        });
    }

    for caps in ctor_re().captures_iter(source) {
        let m = caps.get(0).unwrap();
        let cls = caps.get(1).unwrap().as_str();
        let params = caps.get(2).unwrap().as_str().trim();
        let line = line_at(source, m.start());
        if params.is_empty() {
            continue;
        }
        for part in params.split(',') {
            let part = part.trim();
            if part.is_empty() {
                continue;
            }
            let cleaned = part.replace("...", " ");
            let tokens: Vec<&str> = cleaned
                .split_whitespace()
                .filter(|t| !t.starts_with('@'))
                .collect();
            if tokens.len() < 2 {
                continue;
            }
            let type_name = simple_type(tokens[tokens.len() - 2]);
            let starts_upper = type_name
                .chars()
                .next()
                .map(|c| c.is_ascii_uppercase())
                .unwrap_or(false);
            if !starts_upper || KEYWORDS.contains(&type_name.as_str()) {
                continue;
            }
            edges.push(Relation {
                source: format!("{rel_path}:{cls}"),
                target: type_name,
                relation_type: "injects".into(),
                status: "derived".into(),
                start_line: Some(line),
            });
        }
    }
    edges
}

fn param_types(params: &str) -> Vec<String> {
    let mut out = Vec::new();
    if params.trim().is_empty() {
        return out;
    }
    for part in params.split(',') {
        let part = part.trim();
        if part.is_empty() {
            continue;
        }
        let cleaned = part.replace("...", " ");
        let tokens: Vec<&str> = cleaned
            .split_whitespace()
            .filter(|t| !t.starts_with('@'))
            .collect();
        if tokens.len() < 2 {
            continue;
        }
        let type_name = simple_type(tokens[tokens.len() - 2]);
        let starts_upper = type_name
            .chars()
            .next()
            .map(|c| c.is_ascii_uppercase())
            .unwrap_or(false);
        if starts_upper && !USES_TYPE_SKIP.contains(&type_name.as_str()) {
            out.push(type_name);
        }
    }
    out
}

pub fn parse_type_uses(source: &str, rel_path: &str) -> Vec<Relation> {
    let mut edges = Vec::new();
    let mut seen: HashSet<(String, String, usize)> = HashSet::new();
    let stem = Path::new(rel_path)
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or("module");

    for caps in method_sig_re().captures_iter(source) {
        let m = caps.get(0).unwrap();
        let ret = simple_type(caps.get(1).unwrap().as_str());
        let method = caps.get(2).unwrap().as_str();
        let params = caps.get(3).unwrap().as_str();
        if KEYWORDS.contains(&method) {
            continue;
        }
        let owner = enclosing_type(source, m.start()).unwrap_or_else(|| stem.to_string());
        if method == owner {
            continue;
        }
        let line = line_at(source, m.start());
        let mut types = Vec::new();
        let ret_upper = ret
            .chars()
            .next()
            .map(|c| c.is_ascii_uppercase())
            .unwrap_or(false);
        if ret_upper && !USES_TYPE_SKIP.contains(&ret.as_str()) {
            types.push(ret);
        }
        types.extend(param_types(params));
        for type_name in types {
            if !seen.insert((owner.clone(), type_name.clone(), line)) {
                continue;
            }
            edges.push(Relation {
                source: format!("{rel_path}:{owner}"),
                target: type_name,
                relation_type: "uses_type".into(),
                status: "derived".into(),
                start_line: Some(line),
            });
        }
    }
    edges
}

pub fn parse_calls(source: &str, rel_path: &str) -> Vec<Relation> {
    let field_types: HashMap<String, String> = extract_fields(source)
        .into_iter()
        .map(|(typ, name, _, _, _)| (name, typ))
        .collect();
    let mut edges = Vec::new();
    let mut seen: HashSet<(String, String, usize)> = HashSet::new();
    for caps in call_re().captures_iter(source) {
        let m = caps.get(0).unwrap();
        let target = caps.get(1).unwrap().as_str();
        let leaf = target.rsplit('.').next().unwrap_or(target);
        if KEYWORDS.contains(&leaf) || KEYWORDS.contains(&target) {
            continue;
        }
        let line = line_at(source, m.start());
        let owner_type = enclosing_type(source, m.start()).unwrap_or_else(|| "module".into());
        let owner_method = enclosing_method(source, m.start()).unwrap_or_else(|| "module".into());
        let source_sym = format!("{rel_path}:{owner_type}.{owner_method}");

        let mut resolved = target.to_string();
        if let Some((recv, meth)) = target.rsplit_once('.') {
            if let Some(ft) = field_types.get(recv) {
                resolved = format!("{ft}.{meth}");
            } else if recv == "this" && owner_type != "module" {
                resolved = format!("{owner_type}.{meth}");
            }
        }
        let resolved_leaf = resolved.rsplit('.').next().unwrap_or(&resolved);
        if resolved_leaf == owner_method {
            continue;
        }
        if resolved == owner_type
            || resolved == format!("{owner_type}.{owner_type}")
            || resolved_leaf == owner_type
        {
            continue;
        }
        if !seen.insert((source_sym.clone(), resolved.clone(), line)) {
            continue;
        }
        edges.push(Relation {
            source: source_sym,
            target: resolved,
            relation_type: "calls".into(),
            status: "derived".into(),
            start_line: Some(line),
        });
    }
    edges
}

pub fn parse_relations(source: &str, rel_path: &str) -> Vec<Relation> {
    let mut edges = parse_imports(source, rel_path);
    edges.extend(parse_injections(source, rel_path));
    edges.extend(parse_type_uses(source, rel_path));
    edges.extend(parse_calls(source, rel_path));
    edges
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_java_login_and_spring_edges() {
        let src = r#"
public class OwnerController extends BaseController implements Serializable {
    @Autowired
    private OwnerRepository owners;

    public OwnerController(VisitRepository visits) {
    }

    public Owner findOwner(PetType kind) {
        return owners.findById(1);
    }
}
"#;
        let syms = parse_symbols(src, "OwnerController.java");
        assert!(syms.iter().any(|s| s.name == "OwnerController" && s.kind == "class"));
        assert!(syms.iter().any(|s| s.name == "findOwner"));

        let rels = parse_relations(src, "OwnerController.java");
        assert!(rels.iter().any(|r| r.relation_type == "inherits" && r.target == "BaseController"));
        assert!(rels.iter().any(|r| r.relation_type == "implements" && r.target == "Serializable"));
        assert!(rels.iter().any(|r| r.relation_type == "injects" && r.target == "OwnerRepository"));
        assert!(rels.iter().any(|r| r.relation_type == "injects" && r.target == "VisitRepository"));
        assert!(rels.iter().any(|r| r.relation_type == "uses_type" && r.target == "Owner"));
        assert!(rels.iter().any(|r| r.relation_type == "uses_type" && r.target == "PetType"));
        assert!(rels.iter().any(|r| r.relation_type == "calls" && r.target == "OwnerRepository.findById"));
    }
}
