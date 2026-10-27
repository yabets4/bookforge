# Contributing to BookForge

Thank you for your interest in contributing to **BookForge**!

## Development Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yabets4/bookforge.git
   cd bookforge
   ```

2. **Python Virtual Environment**:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate

   pip install -r requirements.txt
   ```

3. **Running the Test Suite**:
   ```bash
   python test_parser.py
   python test_packager.py
   python test_integration.py
   ```

4. **Running the Server**:
   ```bash
   python run.py
   ```

5. **Building the Android Client**:
   ```bash
   cd mobile
   npm install
   node copy-assets.js
   npx cap sync android
   cd android
   ./gradlew assembleDebug
   ```

## Pull Request Guidelines

- Ensure all existing unit and integration tests pass before opening a PR.
- Add test coverage for any new document parsing formats or TTS engines.
- Write clear, concise commit messages.
- Respect the existing code style and formatting conventions.

## License

By contributing to BookForge, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
