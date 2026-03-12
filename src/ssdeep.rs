#![allow(clippy::collapsible_if)]
use pyo3::exceptions::PyValueError;
use pyo3::{PyResult, pyclass, pymethods};


#[pyclass]
pub struct SsdeepHasher {
    hasher: ssdeep::Generator
}

#[pymethods]
impl SsdeepHasher {
    #[new]
    #[pyo3(signature = (fixed_length=None))]
    pub fn py_new(fixed_length: Option<u64>) -> PyResult<Self> {
        let mut hasher = ssdeep::Generator::new();
        if let Some(length) = fixed_length {
            if let Err(err) = hasher.set_fixed_input_size(length) {
                return Err(PyValueError::new_err(format!("Could not build ssdeep hasher with length {length}: {err}")))
            }
        }
        Ok(Self{ hasher })
    }

    pub fn update(&mut self, data: &[u8]) {
        self.hasher.update(data);
    }

    pub fn digest(&self) -> PyResult<String> {
        match self.hasher.finalize() {
            Ok(digest) => Ok(digest.to_string()),
            Err(err) => Err(PyValueError::new_err(format!("Could not finish ssdeep hash: {err}"))),
        }
    }
}

