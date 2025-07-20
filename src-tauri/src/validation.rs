use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationError {
    pub field: String,
    pub message: String,
    pub code: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationResult {
    pub is_valid: bool,
    pub errors: Vec<ValidationError>,
}

impl ValidationResult {
    pub fn valid() -> Self {
        Self { is_valid: true, errors: Vec::new() }
    }

    pub fn invalid(errors: Vec<ValidationError>) -> Self {
        Self { is_valid: false, errors }
    }

    pub fn add_error(&mut self, error: ValidationError) {
        self.is_valid = false;
        self.errors.push(error);
    }
}

pub trait Validator<T> {
    fn validate(&self, value: &T) -> ValidationResult;
}

pub struct DataIntegrityChecker {
    checks: HashMap<String, Box<dyn Fn() -> ValidationResult>>,
}

impl DataIntegrityChecker {
    pub fn new() -> Self {
        Self { checks: HashMap::new() }
    }

    pub fn add_check<F>(&mut self, name: &str, check: F)
    where F: Fn() -> ValidationResult + 'static,
    {
        self.checks.insert(name.to_string(), Box::new(check));
    }

    pub fn run_checks(&self) -> HashMap<String, ValidationResult> {
        let mut results = HashMap::new();
        for (name, check) in &self.checks {
            results.insert(name.clone(), check());
        }
        results
    }

    pub fn is_valid(&self) -> bool {
        self.run_checks().values().all(|result| result.is_valid)
    }
}