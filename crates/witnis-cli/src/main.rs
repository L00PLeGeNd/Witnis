use std::path::PathBuf;
use std::process::ExitCode;

use clap::{Parser, Subcommand};
use witnis_core::{iter_source_files, scan_source_digests};

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
    }
}
