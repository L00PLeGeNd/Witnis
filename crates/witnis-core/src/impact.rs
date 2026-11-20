use std::collections::HashSet;
use std::path::Path;

use serde::Serialize;

use crate::sandbox::SandboxError;
use crate::store::{SearchHit, Store};

#[derive(Debug, Clone, Serialize)]
pub struct ImpactEdge {
    pub source: String,
    pub target: String,
    pub relation_type: String,
    pub status: String,
    pub start_line: Option<usize>,
    pub impact_level: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct ImpactReport {
    pub status: String,
    pub repository: Option<String>,
    pub root_path: Option<String>,
    pub target: String,
    pub definitions: Vec<SearchHit>,
    pub direct: Vec<ImpactEdge>,
    pub transitive: Vec<ImpactEdge>,
}

fn leaf_symbol(s: &str) -> &str {
    let tail = s.rsplit(':').next().unwrap_or(s);
    tail.rsplit('.').next().unwrap_or(tail)
}

pub fn analyze_impact_db(
    db_path: &Path,
    target: &str,
    limit: usize,
) -> Result<ImpactReport, SandboxError> {
    let store = Store::open(db_path)?;
    let meta = store.latest_repo_meta()?;
    let (repo_name, root_path, repo_id) = match meta {
        Some((n, r, id)) => (Some(n), Some(r), id),
        None => {
            return Ok(ImpactReport {
                status: "failed".into(),
                repository: None,
                root_path: None,
                target: target.to_string(),
                definitions: Vec::new(),
                direct: Vec::new(),
                transitive: Vec::new(),
            })
        }
    };

    let defs = store.search(target, 10)?;
    let all_edges = store.list_relations(repo_id, 5000)?;
    let target_leaf = leaf_symbol(target);

    let mut direct = Vec::new();
    let mut subclasses = Vec::new();
    let mut seen_direct: HashSet<(String, String, String, Option<usize>)> = HashSet::new();

    for e in &all_edges {
        let e_target_leaf = leaf_symbol(&e.target);
        if e.target == target || e_target_leaf == target_leaf {
            let key = (
                e.source.clone(),
                e.target.clone(),
                e.relation_type.clone(),
                e.start_line,
            );
            if seen_direct.insert(key) {
                if e.relation_type == "inherits" {
                    subclasses.push(leaf_symbol(&e.source).to_string());
                }
                direct.push(ImpactEdge {
                    source: e.source.clone(),
                    target: e.target.clone(),
                    relation_type: e.relation_type.clone(),
                    status: e.status.clone(),
                    start_line: e.start_line,
                    impact_level: "Direct".into(),
                });
            }
        }
    }

    let mut transitive = Vec::new();
    let mut seen_trans: HashSet<(String, String, String, Option<usize>)> = HashSet::new();
    for sub in &subclasses {
        for e in &all_edges {
            if e.relation_type == "uses_type" && leaf_symbol(&e.target) == sub {
                let key = (
                    e.source.clone(),
                    e.target.clone(),
                    e.relation_type.clone(),
                    e.start_line,
                );
                if seen_trans.insert(key) {
                    transitive.push(ImpactEdge {
                        source: e.source.clone(),
                        target: e.target.clone(),
                        relation_type: e.relation_type.clone(),
                        status: "derived".into(),
                        start_line: e.start_line,
                        impact_level: "Transitive".into(),
                    });
                }
            }
        }
    }

    direct.truncate(limit);
    transitive.truncate(limit);
    let has_signal = !defs.is_empty() || !direct.is_empty() || !transitive.is_empty();

    Ok(ImpactReport {
        status: if has_signal { "success".into() } else { "partial".into() },
        repository: repo_name,
        root_path,
        target: target.to_string(),
        definitions: defs,
        direct,
        transitive,
    })
}
