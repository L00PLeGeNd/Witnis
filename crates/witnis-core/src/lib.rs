//! Witnis core primitives (Rust).
//!
//! Discover, sandbox, hashing, shallow Go/JS/Java parsers.

pub mod discover;
pub mod hash;
pub mod parse;
pub mod sandbox;
pub mod scan;

pub use discover::{iter_source_files, SourceFile};
pub use hash::sha256_file;
pub use parse::{Relation, Symbol};
pub use sandbox::{assert_path_in_root, is_sensitive_path, SandboxError};
pub use scan::{scan_source_digests, FileDigest};
