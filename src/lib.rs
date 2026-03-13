#![allow(clippy::needless_return)]

mod frequency;
mod hashing;
use pyo3::prelude::*;

/// A collection of tools implemented in rust exported for python components of assemblyline
#[pymodule]
pub mod assemblyline_toolbox {
    use pyo3::prelude::*;
    use pyo3::exceptions::PyRuntimeError;

    #[pymodule_export]
    use crate::frequency::BufferedCalculator;
    #[pymodule_export]
    use crate::hashing::SsdeepHasher;
    #[pymodule_export]
    use crate::hashing::TlshHasher;

    #[pyfunction]
    pub fn get_hostip() -> PyResult<String> {
        match local_ip_address::local_ip() {
            Ok(value) => Ok(value.to_string()),
            Err(err) => Err(PyRuntimeError::new_err(format!("Could not resolve local IP address: {err}"))),
        }
    }
}

