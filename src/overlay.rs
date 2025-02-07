use std::time::Instant;
use eframe::egui::{self, Align2, Color32, FontId, Pos2};
use log::{error, info};
use crate::detection::Detection;
use crate::screenshot;

pub type BoundingBox = (f32, f32, f32, f32);

pub struct Overlay {
    detection: Detection,
    lang: String,
    sentences: Vec<(String, BoundingBox)>, // Store sentences and their bounding boxes
    last_update: Instant, // Track time of the last screenshot update
}

impl Overlay {

    // cc is unused for now but can be used to load the fonts for non-latin characters
    pub fn new(_cc: &eframe::CreationContext<'_>, api_key: String, lang: String, sentences: Vec<(String, BoundingBox)>) -> Self {

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
        
        if self.last_update.elapsed().as_secs() < 1 {
            return;
        }

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

impl eframe::App for Overlay {

    // Transparent background
    fn clear_color(&self, _visuals: &egui::Visuals) -> [f32; 4] {
        [0.0, 0.0, 0.0, 0.0]
    }

    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {

        // Call the method to update the screenshot every second
        self.update_screenshot();

        let identifier = "Overlay Text";
        let layer_id = egui::LayerId::new(egui::Order::Foreground, egui::Id::new(identifier));

        // Iterate through the sentences and their bounding boxes
        for (sentence, (min_x, min_y, max_x, max_y)) in self.sentences.iter() {

            if sentence.is_empty() {
                continue;
            }

            // Create a bounding box
            let bounding_box: egui::Rect = egui::Rect::from_min_max(
                egui::Pos2::new(*min_x, *min_y),
                egui::Pos2::new(*max_x, *max_y),
            );

            // Paint the inside of the bounding box black
            ctx.layer_painter(layer_id).rect_filled(
                bounding_box, 
                0.0,
                egui::Color32::from_black_alpha(200),
            );

            let font_size = egui::TextStyle::Body.resolve(&ctx.style()).size + (bounding_box.height() * 0.1);

            let layout = ctx.layer_painter(layer_id).layout(
                sentence.to_string(), 
                FontId { size: font_size, family: egui::FontFamily::Proportional },
                egui::Color32::WHITE, 
                bounding_box.width()
            );

            // Calculate the starting vertical position to center the text in the box
            let total_height = layout.mesh_bounds.height();
            let vertical_offset = (bounding_box.height() - total_height) / 2.0; // Center vertically in the bounding box
            let mut current_y = bounding_box.top() + vertical_offset; // Start from the top with the vertical offset

            // Reduce font size based on number of rows
            let adjusted_font_size = font_size - (layout.rows.len() as f32);
            
            // Render the translated text
            for row in layout.rows.iter() {
                ctx.layer_painter(layer_id).text(
                    Pos2::new(bounding_box.left(), current_y),
                    Align2::LEFT_TOP,
                    row.text(),
                    FontId { size: adjusted_font_size, family: egui::FontFamily::Proportional },
                    Color32::WHITE,
                );
            
                current_y += row.height();
            }
        }

        ctx.request_repaint(); // Needed to force the app to continuously update
    }
}
