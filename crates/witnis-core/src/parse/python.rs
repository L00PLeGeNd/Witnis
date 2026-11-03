//! Python extraction via rustpython-parser AST (empty on syntax errors).

use std::collections::{HashMap, HashSet};

use rustpython_parser::ast::{self, Ranged};
use rustpython_parser::text_size::{TextRange, TextSize};
use rustpython_parser::Parse;

use super::{Relation, Symbol};

const CALL_SKIP: &[&str] = &[
    "bool", "int", "str", "float", "list", "dict", "set", "tuple", "len", "print", "range",
    "type", "isinstance", "getattr", "setattr", "super", "property", "classmethod",
    "staticmethod", "object",
];

struct FnNode<'a> {
    name: String,
    range: TextRange,
    body: &'a [ast::Stmt],
    decorator_list: &'a [ast::Expr],
}

fn as_fn(stmt: &ast::Stmt) -> Option<FnNode<'_>> {
    match stmt {
        ast::Stmt::FunctionDef(f) => Some(FnNode {
            name: f.name.to_string(),
            range: f.range(),
            body: &f.body,
            decorator_list: &f.decorator_list,
        }),
        ast::Stmt::AsyncFunctionDef(f) => Some(FnNode {
            name: f.name.to_string(),
            range: f.range(),
            body: &f.body,
            decorator_list: &f.decorator_list,
        }),
        _ => None,
    }
}

fn line_of(source: &str, offset: TextSize) -> usize {
    let i = offset.to_usize().min(source.len());
    source[..i].bytes().filter(|&b| b == b'\n').count() + 1
}

fn end_line_of(source: &str, range: TextRange) -> usize {
    line_of(source, range.end())
}

fn expr_name(expr: &ast::Expr) -> Option<String> {
    match expr {
        ast::Expr::Name(n) => Some(n.id.to_string()),
        ast::Expr::Attribute(a) => {
            let mut parts = vec![a.attr.to_string()];
            let mut cur = a.value.as_ref();
            loop {
                match cur {
                    ast::Expr::Attribute(inner) => {
                        parts.push(inner.attr.to_string());
                        cur = inner.value.as_ref();
                    }
                    ast::Expr::Name(n) => {
                        parts.push(n.id.to_string());
                        parts.reverse();
                        return Some(parts.join("."));
                    }
                    _ => return None,
                }
            }
        }
        ast::Expr::Call(c) => expr_name(c.func.as_ref()),
        _ => None,
    }
}

fn parse_suite(source: &str, filename: &str) -> Option<ast::Suite> {
    let source = source.trim_start_matches('\u{feff}');
    ast::Suite::parse(source, filename).ok()
}

pub fn parse_symbols(source: &str, rel_path: &str) -> Vec<Symbol> {
    let Some(suite) = parse_suite(source, rel_path) else {
        return Vec::new();
    };
    let mut out = Vec::new();
    for stmt in &suite {
        if let ast::Stmt::ClassDef(cls) = stmt {
            out.push(Symbol {
                name: cls.name.to_string(),
                kind: "class".into(),
                file_path: rel_path.to_string(),
                start_line: line_of(source, cls.range().start()),
                end_line: end_line_of(source, cls.range()),
            });
            for child in &cls.body {
                if let Some(f) = as_fn(child) {
                    out.push(Symbol {
                        name: format!("{}.{}", cls.name, f.name),
                        kind: "method".into(),
                        file_path: rel_path.to_string(),
                        start_line: line_of(source, f.range.start()),
                        end_line: end_line_of(source, f.range),
                    });
                }
            }
        } else if let Some(f) = as_fn(stmt) {
            out.push(Symbol {
                name: f.name,
                kind: "function".into(),
                file_path: rel_path.to_string(),
                start_line: line_of(source, f.range.start()),
                end_line: end_line_of(source, f.range),
            });
        }
    }
    out
}

pub fn parse_imports(source: &str, rel_path: &str) -> Vec<Relation> {
    let Some(suite) = parse_suite(source, rel_path) else {
        return Vec::new();
    };
    let mut edges = Vec::new();
    for stmt in suite {
        match stmt {
            ast::Stmt::Import(imp) => {
                let line = line_of(source, imp.range().start());
                for alias in imp.names {
                    edges.push(Relation {
                        source: rel_path.to_string(),
                        target: alias.name.to_string(),
                        relation_type: "imports".into(),
                        status: "observed".into(),
                        start_line: Some(line),
                    });
                }
            }
            ast::Stmt::ImportFrom(imp) => {
                let line = line_of(source, imp.range().start());
                let module = imp
                    .module
                    .as_ref()
                    .map(|m| m.to_string())
                    .unwrap_or_default();
                for alias in imp.names {
                    let target = if module.is_empty() {
                        alias.name.to_string()
                    } else {
                        format!("{module}.{}", alias.name)
                    };
                    edges.push(Relation {
                        source: rel_path.to_string(),
                        target,
                        relation_type: "imports_from".into(),
                        status: "observed".into(),
                        start_line: Some(line),
                    });
                }
            }
            _ => {}
        }
    }
    edges
}

pub fn parse_inheritance(source: &str, rel_path: &str) -> Vec<Relation> {
    let Some(suite) = parse_suite(source, rel_path) else {
        return Vec::new();
    };
    let mut edges = Vec::new();
    for stmt in suite {
        let ast::Stmt::ClassDef(cls) = stmt else {
            continue;
        };
        let line = line_of(source, cls.range().start());
        for base in &cls.bases {
            let Some(name) = expr_name(base) else {
                continue;
            };
            if name == "object" {
                continue;
            }
            edges.push(Relation {
                source: format!("{rel_path}:{}", cls.name),
                target: name,
                relation_type: "inherits".into(),
                status: "observed".into(),
                start_line: Some(line),
            });
        }
    }
    edges
}

pub fn parse_decorators(source: &str, rel_path: &str) -> Vec<Relation> {
    let Some(suite) = parse_suite(source, rel_path) else {
        return Vec::new();
    };
    let mut edges = Vec::new();

    let mut emit = |owner: String, decorators: &[ast::Expr], line: usize| {
        for dec in decorators {
            let Some(name) = expr_name(dec) else {
                continue;
            };
            edges.push(Relation {
                source: format!("{rel_path}:{owner}"),
                target: name,
                relation_type: "decorated_by".into(),
                status: "observed".into(),
                start_line: Some(line),
            });
        }
    };

    for stmt in &suite {
        if let ast::Stmt::ClassDef(cls) = stmt {
            emit(
                cls.name.to_string(),
                &cls.decorator_list,
                line_of(source, cls.range().start()),
            );
            for child in &cls.body {
                if let Some(f) = as_fn(child) {
                    emit(
                        format!("{}.{}", cls.name, f.name),
                        f.decorator_list,
                        line_of(source, f.range.start()),
                    );
                }
            }
        } else if let Some(f) = as_fn(stmt) {
            emit(f.name, f.decorator_list, line_of(source, f.range.start()));
        }
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
        let base = edge
            .target
            .split('.')
            .next_back()
            .unwrap_or(&edge.target)
            .to_string();
        class_bases.entry(cls).or_default().push(base);
    }

    let mut edges = Vec::new();
    for (cls, methods) in &class_methods {
        for base in class_bases.get(cls).into_iter().flatten() {
            let base_methods: Option<HashSet<&str>> = class_methods
                .get(base)
                .map(|ms| ms.iter().map(|(m, _)| m.as_str()).collect());
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

fn walk_calls(
    stmts: &[ast::Stmt],
    source: &str,
    owner: &str,
    edges: &mut Vec<Relation>,
    seen: &mut HashSet<(String, String, usize)>,
    skip: &HashSet<&str>,
) {
    for stmt in stmts {
        if let Some(f) = as_fn(stmt) {
            walk_calls(f.body, source, owner, edges, seen, skip);
            continue;
        }
        match stmt {
            ast::Stmt::ClassDef(c) => walk_calls(&c.body, source, owner, edges, seen, skip),
            ast::Stmt::If(i) => {
                walk_calls(&i.body, source, owner, edges, seen, skip);
                walk_calls(&i.orelse, source, owner, edges, seen, skip);
            }
            ast::Stmt::For(f) => {
                walk_calls(&f.body, source, owner, edges, seen, skip);
                walk_calls(&f.orelse, source, owner, edges, seen, skip);
            }
            ast::Stmt::While(w) => {
                walk_calls(&w.body, source, owner, edges, seen, skip);
                walk_calls(&w.orelse, source, owner, edges, seen, skip);
            }
            ast::Stmt::With(w) => walk_calls(&w.body, source, owner, edges, seen, skip),
            ast::Stmt::Try(t) => {
                walk_calls(&t.body, source, owner, edges, seen, skip);
                walk_calls(&t.orelse, source, owner, edges, seen, skip);
                walk_calls(&t.finalbody, source, owner, edges, seen, skip);
                for h in &t.handlers {
                    let ast::ExceptHandler::ExceptHandler(eh) = h;
                    walk_calls(&eh.body, source, owner, edges, seen, skip);
                }
            }
            ast::Stmt::Return(r) => {
                if let Some(v) = &r.value {
                    collect_call_expr(v, source, owner, edges, seen, skip);
                }
            }
            ast::Stmt::Expr(e) => collect_call_expr(&e.value, source, owner, edges, seen, skip),
            ast::Stmt::Assign(a) => collect_call_expr(&a.value, source, owner, edges, seen, skip),
            ast::Stmt::AnnAssign(a) => {
                if let Some(v) = &a.value {
                    collect_call_expr(v, source, owner, edges, seen, skip);
                }
            }
            ast::Stmt::AugAssign(a) => {
                collect_call_expr(&a.value, source, owner, edges, seen, skip)
            }
            _ => {}
        }
    }
}

fn collect_call_expr(
    expr: &ast::Expr,
    source: &str,
    owner: &str,
    edges: &mut Vec<Relation>,
    seen: &mut HashSet<(String, String, usize)>,
    skip: &HashSet<&str>,
) {
    match expr {
        ast::Expr::Call(c) => {
            if let Some(target) = expr_name(c.func.as_ref()) {
                let head = target.split('.').next().unwrap_or(&target);
                if !skip.contains(head) && !skip.contains(target.as_str()) {
                    let line = line_of(source, c.range().start());
                    if seen.insert((owner.to_string(), target.clone(), line)) {
                        edges.push(Relation {
                            source: owner.to_string(),
                            target,
                            relation_type: "calls".into(),
                            status: "observed".into(),
                            start_line: Some(line),
                        });
                    }
                }
            }
            for arg in &c.args {
                collect_call_expr(arg, source, owner, edges, seen, skip);
            }
            for kw in &c.keywords {
                collect_call_expr(&kw.value, source, owner, edges, seen, skip);
            }
        }
        ast::Expr::BoolOp(b) => {
            for v in &b.values {
                collect_call_expr(v, source, owner, edges, seen, skip);
            }
        }
        ast::Expr::BinOp(b) => {
            collect_call_expr(&b.left, source, owner, edges, seen, skip);
            collect_call_expr(&b.right, source, owner, edges, seen, skip);
        }
        ast::Expr::UnaryOp(u) => collect_call_expr(&u.operand, source, owner, edges, seen, skip),
        ast::Expr::Compare(c) => {
            collect_call_expr(&c.left, source, owner, edges, seen, skip);
            for comp in &c.comparators {
                collect_call_expr(comp, source, owner, edges, seen, skip);
            }
        }
        ast::Expr::IfExp(i) => {
            collect_call_expr(&i.test, source, owner, edges, seen, skip);
            collect_call_expr(&i.body, source, owner, edges, seen, skip);
            collect_call_expr(&i.orelse, source, owner, edges, seen, skip);
        }
        ast::Expr::Attribute(a) => collect_call_expr(&a.value, source, owner, edges, seen, skip),
        ast::Expr::Subscript(s) => {
            collect_call_expr(&s.value, source, owner, edges, seen, skip);
            collect_call_expr(&s.slice, source, owner, edges, seen, skip);
        }
        ast::Expr::List(l) => {
            for e in &l.elts {
                collect_call_expr(e, source, owner, edges, seen, skip);
            }
        }
        ast::Expr::Tuple(t) => {
            for e in &t.elts {
                collect_call_expr(e, source, owner, edges, seen, skip);
            }
        }
        ast::Expr::Dict(d) => {
            for v in d.values.iter() {
                collect_call_expr(v, source, owner, edges, seen, skip);
            }
        }
        _ => {}
    }
}

pub fn parse_calls(source: &str, rel_path: &str) -> Vec<Relation> {
    let Some(suite) = parse_suite(source, rel_path) else {
        return Vec::new();
    };
    let skip: HashSet<&str> = CALL_SKIP.iter().copied().collect();
    let mut edges = Vec::new();
    let mut seen = HashSet::new();

    for stmt in &suite {
        if let ast::Stmt::ClassDef(cls) = stmt {
            for child in &cls.body {
                if let Some(f) = as_fn(child) {
                    let owner = format!("{rel_path}:{}.{}", cls.name, f.name);
                    walk_calls(f.body, source, &owner, &mut edges, &mut seen, &skip);
                }
            }
        } else if let Some(f) = as_fn(stmt) {
            let owner = format!("{rel_path}:{}", f.name);
            walk_calls(f.body, source, &owner, &mut edges, &mut seen, &skip);
        }
    }
    edges
}

/// All Python relations for indexing.
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
        let login = syms.iter().find(|s| s.name == "AuthService.login").unwrap();
        assert!(login.end_line >= login.start_line);
    }

    #[test]
    fn parses_inheritance_and_overrides() {
        let edges = parse_relations(AUTH, "auth.py");
        assert!(edges.iter().any(|e| {
            e.relation_type == "inherits"
                && e.source == "auth.py:SecureAuth"
                && e.target == "AuthService"
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
