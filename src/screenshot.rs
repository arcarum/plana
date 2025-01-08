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
        .status();

    match status {
        Ok(exit_status) => {
            if exit_status.success() {
                Ok(output_file)
            } else {
                Err(std::io::Error::new(std::io::ErrorKind::Other, "Spectacle command failed"))
            }
        }
        Err(e) => Err(e),
    }
}