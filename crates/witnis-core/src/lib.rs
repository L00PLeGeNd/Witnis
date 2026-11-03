//! Witnis core primitives (Rust).
//!
//! Phase-1 surface: path sandbox, source discovery, content hashing.

pub mod discover;
pub mod hash;
pub mod sandbox;

pub use discover::{iter_source_files, SourceFile};
pub use hash::sha256_file;
pub use sandbox::{assert_path_in_root, is_sensitive_path, SandboxError};
