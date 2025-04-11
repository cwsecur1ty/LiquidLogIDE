# LiquidIDE

An IDE for creating and managing Liquid templates with Sigma rule integration. LiquidIDE provides a streamlined interface for security professionals to create and test Liquid templates for log analysis and security monitoring.

![needToUploadAScreenshotOneday](needToUploadAScreenshotOneday.png)

## Features

- **Intuitive Interface**: Clean, modern design with a split-pane layout
- **Sigma Rule Integration**: Direct import of Sigma JSON rules
- **Smart Template Generation**: Automatically generates Liquid templates from Sigma rules
- **Real-time Preview**: Instant markdown output preview
- **System-specific Templates**: Pre-built variables for Windows, Linux, Entra ID, and Cloudflare
- **Advanced Editor Features**
- **Template Management**
- **Variable Management**

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Node.js 14.0 or higher (for Liquid template processing)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/LiquidLogIDE.git
   cd LiquidLogIDE
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Node.js dependencies:
   ```bash
   npm install
   ```

5. Run the application:
   ```bash
   python app.py
   ```

6. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Usage

### Creating Templates

1. **Upload Sigma Rule**:
   - Click "Upload Sigma JSON" to import a Sigma rule
   - The company name field will be used in the generated template
   - The template will be automatically generated based on the Sigma rule structure

2. **Manual Editing**:
   - Use the editor to modify the template
   - Insert variables using the sidebar options
   - Use the format button to clean up the template

3. **Template Structure**:
   - Templates use Liquid syntax for processing
   - The basic structure includes conditional sections for single or multiple log entries
   - Fields from the Sigma rule detection section are automatically included
   - The title is extracted from the `runbook.title` field if available

4. **Testing**:
   - Click "Run" to preview the template
   - View the output in the right panel
   - Make adjustments as needed

### Template Management

- **Save**: Click "Save" to store the current template as a .liquid file
- **Load**: Click "Load" to open a saved template
- **Clear**: Use the clear button to reset the editor

### System-specific Features

- Select the appropriate system (Windows, Linux, Entra ID, Cloudflare)
- Access system-specific variables and templates
- Use outcome processing templates for complex scenarios

## Working with Sigma Rules

The application supports importing Sigma rules in JSON format. When uploading a Sigma JSON file:

1. The title of the template is taken from the `runbook.title` field if available, or falls back to the `title` field
2. Fields from the detection rules are automatically extracted and included in the template
3. The template is structured with sections for handling both single and multiple log entries
4. Your company name is inserted into the template text


## Contributing

Contributions are welcome. Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers. 
