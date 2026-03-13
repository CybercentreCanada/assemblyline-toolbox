#![allow(clippy::needless_return)]

mod frequency;
mod hashing;
use pyo3::prelude::*;

/// A collection of tools implemented in rust exported for python components of assemblyline
#[pymodule]
pub mod assemblyline_toolbox {
    #[pymodule_export]
    use crate::frequency::BufferedCalculator;
    #[pymodule_export]
    use crate::hashing::SsdeepHasher;
    #[pymodule_export]
    use crate::hashing::TlshHasher;
}

