use std::path::PathBuf;
use std::process::ExitCode;

use clap::{Parser, Subcommand};
use witnis_core::{
    index_repository, iter_source_files, overview_db, scan_source_digests, search_symbols,
};

#[derive(Parser, Debug)]
#[command(name = "witnis-core", about = "Witnis Rust core utilities")]
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
    }
}
