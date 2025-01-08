use std::env;

use eframe::egui;
use env_logger::Builder;

mod overlay;
mod screenshot;
mod detection;
mod config;

fn main() {

    // Initialize the logger
    Builder::new()
    .parse_filters(&env::var("RUST_LOG").unwrap_or_else(|_| "info".to_string())) // default to info if not set
    .init();

    let config = config::load_config("./config.toml").expect("Failed to load config");
    
    let native_options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_fullscreen(true)
            .with_transparent(true)
            .with_decorations(true)
            .with_always_on_top()
            .with_mouse_passthrough(true)
            .with_resizable(false),
        ..Default::default()
    };

    let _ = eframe::run_native(
        "Overlay Application",
        native_options,
        Box::new(|cc| {
            Ok(Box::new(overlay::Overlay::new(
                cc,
                config.api.gemini,
                config.languages.lang_from,
                Vec::new(),
            )))
        }),
    );
}