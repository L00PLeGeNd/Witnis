use std::path::PathBuf;
use std::process::ExitCode;

use clap::{Parser, Subcommand};
use serde_json::{json, Value};
use witnis_core::{
    analyze_impact_db, index_repository, iter_source_files, overview_db, scan_source_digests,
    search_symbols,
};

#[derive(Parser, Debug)]
#[command(
    name = "witnis-core",
    about = "Witnis Rust core utilities (index/search path — not full CLI)"
)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// List discovered source files (relative paths)
    Discover {
        #[arg(value_name = "ROOT")]
        root: PathBuf,
    },
    /// Emit JSON digests for source files
    Scan {
        #[arg(value_name = "ROOT")]
        root: PathBuf,
    },
    /// Index a repository into SQLite (Rust backend)
    Index {
        #[arg(value_name = "ROOT")]
        root: PathBuf,
        #[arg(long, value_name = "DB")]
        db: PathBuf,
        #[arg(long, default_value_t = false)]
        full: bool,
    },
    /// Search symbols in a Witnis SQLite DB
    Search {
        #[arg(value_name = "QUERY")]
        query: String,
        #[arg(long, value_name = "DB")]
        db: PathBuf,
        #[arg(long, default_value_t = 50)]
        limit: usize,
    },
    /// Summarize an indexed SQLite DB
    Overview {
        #[arg(long, value_name = "DB")]
        db: PathBuf,
    },
    /// Analyze 1-hop Direct and 2-hop Transitive impact for a symbol
    Impact {
        #[arg(value_name = "TARGET")]
        target: String,
        #[arg(long, value_name = "DB")]
        db: PathBuf,
        #[arg(long, default_value_t = 50)]
        limit: usize,
    },
    /// Print shipped vs pip-only command parity (JSON)
    Parity,
}

/// Static parity snapshot for Stage-3 full-binary planning.
fn command_parity() -> Value {
    json!({
        "binary": "witnis-core",
        "full_cli": "witnis (pip)",
        "docs": "docs/rust-full-binary.md",
        "shipped": ["discover", "scan", "index", "search", "overview", "impact", "parity"],
        "pip_only": [
            "look", "trace", "pr-gate", "verify", "plan-verify",
            "loop-init", "mcp", "studio", "bench", "browser-demo", "scene",
            "refresh", "evidence", "capabilities", "change-impact", "explain-change"
        ],
        "next_ports": ["trace", "pr-gate"],
        "phase": "7.1"
    })
}

fn main() -> ExitCode {
    let cli = Cli::parse();
    match cli.command {
        Commands::Discover { root } => match iter_source_files(&root) {
            Ok(files) => {
                for f in files {
                    println!("{}", f.rel_path);
                }
                ExitCode::SUCCESS
            }
            Err(err) => {
                eprintln!("error: {err}");
                ExitCode::FAILURE
            }
        },
        Commands::Scan { root } => match scan_source_digests(&root) {
            Ok(rows) => match serde_json::to_string_pretty(&rows) {
                Ok(text) => {
                    println!("{text}");
                    ExitCode::SUCCESS
                }
                Err(err) => {
                    eprintln!("error: {err}");
                    ExitCode::FAILURE
                }
            },
            Err(err) => {
                eprintln!("error: {err}");
                ExitCode::FAILURE
            }
        },
        Commands::Index { root, db, full } => match index_repository(&root, &db, !full) {
            Ok(stats) => match serde_json::to_string_pretty(&stats) {
                Ok(text) => {
                    println!("{text}");
                    ExitCode::SUCCESS
                }
                Err(err) => {
                    eprintln!("error: {err}");
                    ExitCode::FAILURE
                }
            },
            Err(err) => {
                eprintln!("error: {err}");
                ExitCode::FAILURE
            }
        },
        Commands::Search { query, db, limit } => match search_symbols(&db, &query, limit) {
            Ok(hits) => match serde_json::to_string_pretty(&hits) {
                Ok(text) => {
                    println!("{text}");
                    ExitCode::SUCCESS
                }
                Err(err) => {
                    eprintln!("error: {err}");
                    ExitCode::FAILURE
                }
            },
            Err(err) => {
                eprintln!("error: {err}");
                ExitCode::FAILURE
            }
        },
        Commands::Overview { db } => match overview_db(&db) {
            Ok(stats) => match serde_json::to_string_pretty(&stats) {
                Ok(text) => {
                    println!("{text}");
                    ExitCode::SUCCESS
                }
                Err(err) => {
                    eprintln!("error: {err}");
                    ExitCode::FAILURE
                }
            },
            Err(err) => {
                eprintln!("error: {err}");
                ExitCode::FAILURE
            }
        },
        Commands::Impact { target, db, limit } => match analyze_impact_db(&db, &target, limit) {
            Ok(report) => match serde_json::to_string_pretty(&report) {
                Ok(text) => {
                    println!("{text}");
                    ExitCode::SUCCESS
                }
                Err(err) => {
                    eprintln!("error: {err}");
                    ExitCode::FAILURE
                }
            },
            Err(err) => {
                eprintln!("error: {err}");
                ExitCode::FAILURE
            }
        },
        Commands::Parity => match serde_json::to_string_pretty(&command_parity()) {
            Ok(text) => {
                println!("{text}");
                ExitCode::SUCCESS
            }
            Err(err) => {
                eprintln!("error: {err}");
                ExitCode::FAILURE
            }
        },
    }
}

#[cfg(test)]
mod tests {
    use super::command_parity;

    #[test]
    fn parity_lists_core_and_pip_only() {
        let p = command_parity();
        let shipped = p["shipped"].as_array().expect("shipped");
        assert!(shipped.iter().any(|v| v.as_str() == Some("parity")));
        assert!(shipped.iter().any(|v| v.as_str() == Some("index")));
        let pip = p["pip_only"].as_array().expect("pip_only");
        assert!(pip.iter().any(|v| v.as_str() == Some("pr-gate")));
        assert!(pip.iter().any(|v| v.as_str() == Some("verify")));
        assert!(shipped.iter().any(|v| v.as_str() == Some("impact")));
        assert_eq!(p["phase"], "7.1");
        assert_eq!(p["docs"], "docs/rust-full-binary.md");
    }
}
