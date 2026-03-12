//! Utilities used for fast byte counting in python
//!
//! This is duplicated from the assemblyline-server crate due to its simplicity.

use pyo3::{pyclass, pymethods};


/// A counter that accumulates byte frequencies in order to calculate entropy
#[pyclass]
pub struct BufferedCalculator {
    counts: Box<[u64; 256]>,
    length: u64,
}


#[pymethods]
impl BufferedCalculator {
    #[new]
    pub fn py_new() -> Self {
        Self {
            counts: Box::new([0; 256]),
            length: 0,
        }
    }

    pub fn len(&self) -> u64 {
        self.length
    }

    pub fn entropy(&self) -> f64 {
        if self.length == 0 {
            return 0.0;
        }

        let length = self.length as f64;

        let mut entropy = 0.0;
        for v in self.counts.iter() {
            let prob = *v as f64 / length;
            if prob != 0.0 {
                entropy += prob * prob.log2();
            }
        }

        entropy *= -1.0;

        // Make sure we don't return -0.0. Just keep things pretty.
        if entropy == -0.0 {
            entropy = 0.0;
        }

        return entropy
    }

    pub fn update(&mut self, data: &[u8]) {
        self.length += data.len() as u64;
        for byte in data {
            self.counts[*byte as usize] += 1;
        }
    }
}
