use pyo3::{types::{PyAnyMethods, PyModule}, IntoPyObject, PyObject, PyResult, Python};

pub struct Detection {
    api_key: String,
    py_class_instance: Option<PyObject>,
}

impl Detection {

    pub fn new(api_key: String) -> Self {
        Detection {
            api_key,
            py_class_instance: None,
        }
    }

    pub fn process_image(&mut self, lang: &str, image_path: &str) -> PyResult<Vec<(String, (u32, u32, u32, u32))>> {

        pyo3::prepare_freethreaded_python();
        Python::with_gil(|py| {
            
            // Import the Python script without the .py extension
            let sys = py.import("sys")?.unbind();
            let _ = sys.getattr(py, "path")?.call_method1(py, "insert", (0, "./python_scripts"))?;
    
            let module = PyModule::import(py, "text_detector_and_translator")?;

            if self.py_class_instance.is_none() {
                let class = module.getattr("TextDetectorAndTranslator")?.into_pyobject(py)?.unbind();
                let instance = class.call1(py, (lang, self.api_key.clone()))?;
                self.py_class_instance = Some(instance);
            }
    
            let py_class_instance = self.py_class_instance.as_ref().unwrap();

            // Call the 'detect_and_translate' method on the instance
            let result: Vec<(String, (u32, u32, u32, u32))> = py_class_instance
                .getattr(py, "detect_and_translate")?
                .call1(py, (image_path,))?
                .extract(py)?;

            Ok(result)
        })
    }
}