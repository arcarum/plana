use serde::Deserialize;
use std::fs;

#[derive(Deserialize, Default)]
pub struct Config {

    #[serde(default)]
    pub api: ApiConfig,

    pub languages: LanguagesConfig,
}

#[derive(Deserialize, Default)]
pub struct ApiConfig {

    #[serde(default)]
    pub gemini: String,
}

#[derive(Deserialize, Default)]
pub struct LanguagesConfig {
    // pub lang_to: String, // Currently unused, always default to English
    pub lang_from: String,
}

// Function to read and parse the config TOML file
pub fn load_config(path: &str) -> Result<Config, toml::de::Error> {
    let content = fs::read_to_string(path).expect("Failed to read the TOML file");
    toml::de::from_str(&content) // Deserialize the TOML content into the Config struct
}