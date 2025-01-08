## Plana - A Real-time Text Detection and Translation Overlay
A Rust-based application for Wayland that integrates Python for real-time text detection and translation using EasyOCR and Gemini.

The application works by periodically taking a screenshot using **Spectacle**, detecting the text in the required language using **EasyOCR**, translating the text using the **Gemini** API, and then displaying the translated text as an overlay on the display.

## Requirements

- **Spectacle**: For taking periodic screenshots.
- **EasyOCR**: For detecting text in images.
- **Gemini API**: For translating detected text.

## How to Run

1. Install [EasyOCR](https://github.com/JaidedAI/EasyOCR).

2. Install **Spectacle** for taking screenshots. On **Arch Linux**, you can install it using:

    ```bash
    pacman -S spectacle
    ```

3. Clone the repository:

    ```bash
    git clone https://github.com/arcarum/plana.git
    cd plana/
    ```

4. Configure the language you want to detect in `config.toml`. Replace `lang_from` with the required language.

5. Add your **Gemini API key** in `config.toml` under the `gemini` field.

    Example:

    ```toml
    [api]
    gemini = "your_api_key_here"

    [languages]
    lang_from = "en"  # Set the language to detect
    ```
6. Build and run the project using Cargo:

    ```bash
    cargo run
    ```

7. On **KDE**, you may need to ensure that the application stays on top of others by right-clicking the application icon in the taskbar and selecting `More` > `Keep Above Others`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
