//! Witnis core primitives (Rust).
//!
//! Discover, sandbox, hashing, shallow parsers, SQLite index/search.

pub mod discover;
pub mod hash;
pub mod impact;
pub mod index;
pub mod overview;
pub mod parse;
pub mod sandbox;
pub mod scan;
pub mod search;
pub mod store;

pub use discover::{iter_source_files, SourceFile};
pub use hash::sha256_file;
pub use impact::{analyze_impact_db, ImpactEdge, ImpactReport};
pub use index::{index_repository, IndexStats};
pub use overview::{overview_db, Overview};
pub use parse::{Relation, Symbol};
pub use sandbox::{assert_path_in_root, is_sensitive_path, SandboxError};
pub use scan::{scan_source_digests, FileDigest};
pub use search::search_symbols;
pub use store::SearchHit;
