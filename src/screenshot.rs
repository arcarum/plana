use std::process::Command;
use std::io::Result;

pub fn capture_screenshot(output_directory: &str) -> Result<String> {
    let output_file = format!("{}/screenshot.jpg", output_directory);

    let status = Command::new("spectacle")
        .arg("-b") // background
        .arg("-n") // no notification
        .arg("-a") // active window
        .arg("-o") // output to
        .arg(&output_file)
        .status()?;

    match status.success() {
        true => Ok(output_file),
        false => Err(std::io::Error::new(std::io::ErrorKind::Other, "Spectacle command failed")),
    }
}