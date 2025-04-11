# LiquidIDE

An IDE for creating and managing Liquid templates with Sigma rule integration.

## Features

- **Intuitive Interface**: Clean, modern design with a split-pane layout
- **Sigma Rule Integration**: Direct import of Sigma JSON rules
- **Smart Template Generation**: Automatically generates Liquid templates from Sigma rules
- **Real-time Preview**: Instant markdown output preview
- **System-specific Templates**: Pre-built templates for Windows, Linux, Entra ID, and Cloudflare
- **Advanced Editor Features**
- **Template Management**
- **Variable Management**

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/cwsecur1ty/LiquidIDE.git
   cd LiquidIDE
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Usage

### Creating Templates

1. **Upload Sigma Rule**:
   - Click "Upload Sigma JSON" to import a Sigma rule
   - Select the number of log entries (1-5)
   - The template will be automatically generated

2. **Manual Editing**:
   - Use the editor to modify the template
   - Insert variables using the sidebar options
   - Use the format button to clean up the template

3. **Testing**:
   - Click "Run" to process the template
   - View the markdown output in the right panel
   - Make adjustments as needed

### Template Management

- **Save**: Click "Save" to store the current template
- **Load**: Click "Load" to open a saved template
- **Clear**: Use the clear button to reset the editor

### System-specific Features

- Select the appropriate system (Windows, Linux, Entra ID, Cloudflare)
- Access system-specific variables and templates
- Use outcome processing templates for complex scenarios

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Sigma](https://github.com/SigmaHQ/sigma) for the rule format
- [CodeMirror](https://codemirror.net/) for the editor
- [Font Awesome](https://fontawesome.com/) for icons

## Support

For support, please open an issue in the GitHub repository or contact the maintainers. 
