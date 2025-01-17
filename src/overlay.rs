use std::time::Instant;
use eframe::egui::{self};
use log::{error, info};
use crate::detection::Detection;
use crate::screenshot;

pub struct Overlay {
    detection: Detection,
    lang: String,
    sentences: Vec<(String, (u32, u32, u32, u32))>, // Store sentences and their bounding boxes
    last_update: Instant, // Track time of the last screenshot update
}

impl Overlay {

    // cc is unused for now but can be used to load the fonts for non-latin characters
    pub fn new(_cc: &eframe::CreationContext<'_>, api_key: String, lang: String, sentences: Vec<(String, (u32, u32, u32, u32))>) -> Self {

        Overlay {
            detection: Detection::new(api_key),
            lang,
            sentences,
            last_update: Instant::now(),
        }
    }

    // Trigger screenshot capture and processing every second
    fn update_screenshot(&mut self) {

        let output_directory = "/tmp";
        
        if self.last_update.elapsed().as_secs() >= 1 {
            match screenshot::capture_screenshot(output_directory) {
                Ok(output) => {
                    info!("Screenshot saved to: {}", output);
                    self.sentences = self.detection.process_image(&self.lang, &output).unwrap_or_default();
                }
                Err(e) => error!("Error capturing screenshot: {}", e),
            }
            
            self.last_update = Instant::now(); // Reset last update time to the current time

            info!("Updating overlay text!"); // Log is here since the update function runs 60 times per second
        }
    }
}

impl eframe::App for Overlay {

    // Transparent background
    fn clear_color(&self, _visuals: &egui::Visuals) -> [f32; 4] {
        [0.0, 0.0, 0.0, 0.0]
    }

    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {

        // Call the method to update the screenshot every second
        self.update_screenshot();

        // Iterate through the sentences and their bounding boxes
        for (sentence, (min_x, min_y, max_w, max_h)) in self.sentences.iter() {

            if sentence.is_empty() {
                continue;
            }

            let identifier = "Overlay Text";
            let layer_id = egui::LayerId::new(egui::Order::Foreground, egui::Id::new(identifier));

            // Create a bounding box from (x, y, w, h)
            let bounding_box: egui::Rect = egui::Rect::from_min_max(
                egui::Pos2::new(*min_x as f32, *min_y as f32),
                egui::Pos2::new(*max_w as f32 + *min_x as f32, *max_h as f32 + *min_y as f32),
            );

            // Paint the inside of the bounding box black
            ctx.layer_painter(layer_id).rect_filled(
                bounding_box, 
                0.0,
                egui::Color32::from_black_alpha(200),
            );

            let margin_factor = 0.5;
            let font_size = bounding_box.height() * margin_factor;

            // Render the sentence text 
            ctx.layer_painter(layer_id).text(
                bounding_box.left_center(),
                egui::Align2::LEFT_CENTER,
                sentence,
                egui::FontId { size: font_size.round(), family: egui::FontFamily::Proportional },
                egui::Color32::WHITE,
            );
        }

        ctx.request_repaint(); // Needed to force the app to continuously update
    }
}
