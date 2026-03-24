#![allow(clippy::collapsible_if)]
use pyo3::exceptions::{PyTypeError, PyValueError};
use pyo3::types::{PyAnyMethods, PyBytes, PyBytesMethods, PyStringMethods, PyTypeMethods};
use pyo3::{Bound, PyAny, PyResult, pyclass, pymethods};


fn get_data<'a>(data: &Bound<'a, PyAny>) -> PyResult<Bound<'a, PyBytes>> {
    if let Ok(string) = data.cast() {
        Ok(string.encode_utf8()?)
    } else if let Ok(bytes) = data.cast::<PyBytes>() {
        Ok(bytes.clone())
    } else {
        Err(PyTypeError::new_err(format!("Can't convert from {} to bytes", data.get_type().name()?)))
    }
}

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

    #[staticmethod]
    pub fn hash<'py>(data: Bound<'py, PyAny>) -> PyResult<String> {
        let data = get_data(&data)?;

        let mut hasher = Self::py_new(Some(data.len()? as u64))?;
        hasher.update(data.as_bytes());
        hasher.digest()
    }
}


#[pyclass]
pub struct TlshHasher {
    hasher: tlsh2::TlshDefaultBuilder,
}

#[pymethods]
impl TlshHasher {
    #[new]
    pub fn py_new() -> Self {
        Self{ hasher: tlsh2::TlshDefaultBuilder::new() }
    }

    pub fn update(&mut self, data: &[u8]) {
        self.hasher.update(data);
    }

    pub fn digest(&self) -> Option<String> {
        self.hasher.build()
            .map(|hash| String::from_utf8_lossy(hash.hash().as_slice()).to_string())
    }

    #[staticmethod]
    pub fn hash(data: Bound<'_, PyAny>) -> PyResult<Option<String>> {
        let data = get_data(&data)?;

        let mut hasher = Self::py_new();
        hasher.update(data.as_bytes());
        Ok(hasher.digest())
    }
}

