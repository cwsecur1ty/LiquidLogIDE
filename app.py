from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os
import re
from werkzeug.utils import secure_filename
import uuid
import subprocess
import tempfile

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TEMPLATES_FOLDER'] = 'Liquid Templates'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload and templates folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMPLATES_FOLDER'], exist_ok=True)

def extract_variables_from_rule(rule):
    # Split the rule by AND to get individual conditions
    conditions = [cond.strip() for cond in rule.split('AND')]
    variables = []
    
    for condition in conditions:
        # Extract the variable name (everything before the colon)
        match = re.match(r'([^:]+):', condition)
        if match:
            variable = match.group(1).strip()
            variables.append(variable)
    
    return variables

def generate_liquid_template(num_entries, company_name):
    if num_entries == 1:
        return """{% assign log_entries = logs.log %}
# {{ log_entries[0].TargetUserName }} - {{ log_entries[0].TargetDomainName }}

## Overview
- Event ID: {{ log_entries[0].EventType }}
- Target Object: {{ log_entries[0].TargetObject }}
- Subject User: {{ log_entries[0].SubjectUserName }}
- Subject SID: {{ log_entries[0].SubjectUserSid }}

## Details
- Company: {0}
- Event Time: {{ log_entries[0].EventTime }}
- Client IP: {{ log_entries[0].client_ip }}
- Target User: {{ log_entries[0].TargetUserName }}
- Target Domain: {{ log_entries[0].TargetDomainName }}
- Subject User: {{ log_entries[0].SubjectUserName }}
- Subject SID: {{ log_entries[0].SubjectUserSid }}
- Event Type: {{ log_entries[0].EventType }}
- Target Object: {{ log_entries[0].TargetObject }}

## Outcome Processing
{% if log_entries[0].EventType == "4657" %}
- Action: Registry key value modified
- Key: {{ log_entries[0].TargetObject }}
- Value: {{ log_entries[0].NewValue }}
{% endif %}

## Additional Context
- Process ID: {{ log_entries[0].ProcessId }}
- Thread ID: {{ log_entries[0].ThreadId }}
- Computer: {{ log_entries[0].Computer }}
""".format(company_name)
    else:
        return """{% assign log_entries = logs.log %}
# Multiple Events

## Overview
- Company: {0}
- Number of Events: {1}

## Events
{% for log_entry in log_entries %}
### Event {{ forloop.index }}
- Event ID: {{ log_entry.EventType }}
- Target Object: {{ log_entry.TargetObject }}
- Subject User: {{ log_entry.SubjectUserName }}
- Subject SID: {{ log_entry.SubjectUserSid }}

#### Details
- Event Time: {{ log_entry.EventTime }}
- Client IP: {{ log_entry.client_ip }}
- Target User: {{ log_entry.TargetUserName }}
- Target Domain: {{ log_entry.TargetDomainName }}
- Subject User: {{ log_entry.SubjectUserName }}
- Subject SID: {{ log_entry.SubjectUserSid }}
- Event Type: {{ log_entry.EventType }}
- Target Object: {{ log_entry.TargetObject }}

#### Outcome Processing
{% if log_entry.EventType == "4657" %}
- Action: Registry key value modified
- Key: {{ log_entry.TargetObject }}
- Value: {{ log_entry.NewValue }}
{% endif %}

#### Additional Context
- Process ID: {{ log_entry.ProcessId }}
- Thread ID: {{ log_entry.ThreadId }}
- Computer: {{ log_entry.Computer }}
{% endfor %}
""".format(company_name, num_entries)

def process_liquid_template(template, data):
    """Process a Liquid template using Node.js"""
    temp_template_path = None
    temp_data_path = None
    temp_output_path = None
    
    try:
        # Create a temporary file for the template
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.liquid') as temp_template:
            temp_template.write(template)
            temp_template_path = temp_template.name

        # Create a temporary file for the data
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_data:
            # Get the number of logs to simulate from the UI
            # Default to 1 if not present in the request
            log_count = 1
            if 'log_count' in data:
                log_count = int(data['log_count'])
            
            # Create sample data with the appropriate number of log entries
            sample_data = {
                'logs': {
                    'log': []
                }
            }
            
            # Generate multiple sample log entries based on log_count
            for i in range(log_count):
                sample_log = {
                    'EventType': f'Sample Event {i+1}',
                    'TargetObject': f'Sample Target {i+1}',
                    'SubjectUserName': f'Sample User {i+1}',
                    'SubjectUserSid': f'S-1-5-21-123456789-123456789-123456789-{1000+i}',
                    'TargetUserName': f'Sample Target User {i+1}',
                    'TargetDomainName': 'sample.domain',
                    'EventTime': f'2023-06-01T{12+i}:00:00Z',
                    'client_ip': f'192.168.1.{100+i}',
                    'ProcessId': f'{1234+i}',
                    'ThreadId': f'{5678+i}',
                    'Computer': f'SAMPLE-PC-{i+1}',
                    'NewValue': f'Sample Value {i+1}',
                    'MemberName': f'CN=User{i+1},DC=sample,DC=com'
                }
                sample_data['logs']['log'].append(sample_log)
            
            json.dump(sample_data, temp_data)
            temp_data_path = temp_data.name

        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as temp_output:
            temp_output_path = temp_output.name

        # Run the Node.js processor
        process = subprocess.Popen(
            ['node', 'liquid_processor.js', temp_template_path, temp_data_path, temp_output_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            stderr_text = stderr.decode() if stderr else "Unknown error"
            # Log the error for debugging
            print(f"Node.js processor error: {stderr_text}")
            
            # Check if the error file has content
            if os.path.exists(temp_output_path) and os.path.getsize(temp_output_path) > 0:
                with open(temp_output_path, 'r') as f:
                    error_message = f.read()
                raise Exception(error_message)
            else:
                raise Exception(f"Node.js processor failed: {stderr_text}")

        # Read the processed output
        with open(temp_output_path, 'r') as f:
            result = f.read()

        return result

    except Exception as e:
        print(f"Template processing error: {str(e)}")
        raise e
    finally:
        # Clean up temporary files if they exist
        for path in [temp_template_path, temp_data_path, temp_output_path]:
            try:
                if path and os.path.exists(path):
                    os.unlink(path)
            except Exception as cleanup_error:
                print(f"Error cleaning up temp file {path}: {str(cleanup_error)}")

def sigma_to_liquid_template(sigma_data, company_name="Defense.com"):
    """
    Convert a Sigma rule JSON to a Liquid template format
    """
    # Ensure we have a list of rules
    if not isinstance(sigma_data, list):
        sigma_data = [sigma_data]
    
    # Extract the title, prioritizing runbook.title if it exists
    title = None
    if 'runbook' in sigma_data[0] and 'title' in sigma_data[0]['runbook']:
        title = sigma_data[0]['runbook']['title']
    else:
        title = sigma_data[0].get('title', 'Untitled')
    
    # Create the template manually with proper syntax
    template = '{% assign log_entries = logs.log -%}\n'
    template += '{% if log_entries.size == 1 -%}\n'
    template += f'  {company_name} has detected {title}. As part of the investigation, {company_name} observed the following activity:\n\n'
    
    # Extract detection fields from the first rule
    detection_fields = []
    if sigma_data[0].get('detection') and isinstance(sigma_data[0]['detection'], dict):
        # Get key fields from selection sections
        for key, value in sigma_data[0]['detection'].items():
            if key not in ['condition'] and isinstance(value, dict):
                for field in value.keys():
                    if field not in detection_fields and not field.startswith('_'):
                        detection_fields.append(field)
    
    # If no fields were found, use some defaults
    if not detection_fields:
        detection_fields = ["EventType", "TargetObject"]
    
    # Add the field outputs for single event - without bold formatting
    for field in detection_fields:
        template += f'  * {field}: `{{{{ log_entries[0].{field} }}}}`\n'
    
    # Add the multiple events section
    template += '\n{% else -%}\n'
    template += f'  {company_name} has detected {title}. As part of the investigation, {company_name} observed multiple events:\n\n'
    template += '  {% for log_entry in log_entries %}\n'
    
    # Add the field outputs for multiple events - without bold formatting
    for field in detection_fields:
        template += f'  * {field}: `{{{{ log_entry.{field} }}}}`\n'
    
    # Close the template
    template += '  {% endfor -%}\n'
    template += '{% endif -%}\n'
    
    return template

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.endswith('.json'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            with open(filepath, 'r') as f:
                json_data = json.load(f)
            
            # Get company name from form data or use default
            company_name = request.form.get('company_name', 'Defense.com')
            
            # Generate a Liquid template from the Sigma data
            template = sigma_to_liquid_template(json_data, company_name)
            
            # Get title from the JSON data for the response, prioritizing runbook.title
            title = 'Untitled'
            if isinstance(json_data, list):
                if json_data and 'runbook' in json_data[0] and 'title' in json_data[0]['runbook']:
                    title = json_data[0]['runbook']['title']
                else:
                    title = json_data[0].get('title', 'Untitled')
            else:
                if 'runbook' in json_data and 'title' in json_data['runbook']:
                    title = json_data['runbook']['title']
                else:
                    title = json_data.get('title', 'Untitled')
            
            return jsonify({
                'status': 'success',
                'template': template,
                'title': title,
                'company_name': company_name
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            # Clean up the uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/save_template', methods=['POST'])
def save_template():
    try:
        data = request.json
        template_content = data.get('content')
        template_name = data.get('name')
        
        if not template_name:
            return jsonify({'status': 'error', 'message': 'Template name is required'}), 400
            
        # Ensure the filename has .liquid extension
        if not template_name.endswith('.liquid'):
            template_name += '.liquid'
            
        # Sanitize the filename
        safe_name = secure_filename(template_name)
        
        # Save the template
        template_path = os.path.join(app.config['TEMPLATES_FOLDER'], safe_name)
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
            
        return jsonify({
            'status': 'success',
            'message': f'Successfully saved template to {template_path}',
            'path': template_path
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/load_template', methods=['GET'])
def load_template():
    try:
        template_name = request.args.get('name')
        if not template_name:
            return jsonify({'status': 'error', 'message': 'Template name is required'}), 400
            
        # Sanitize the filename
        safe_name = secure_filename(template_name)
        
        # Check if file exists
        template_path = os.path.join(app.config['TEMPLATES_FOLDER'], safe_name)
        if not os.path.exists(template_path):
            return jsonify({'status': 'error', 'message': 'Template not found'}), 404
            
        # Read the template
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return jsonify({
            'status': 'success',
            'content': content,
            'name': template_name
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/list_templates', methods=['GET'])
def list_templates():
    try:
        templates = []
        for filename in os.listdir(app.config['TEMPLATES_FOLDER']):
            if filename.endswith('.liquid'):
                templates.append({
                    'name': filename,
                    'path': os.path.join(app.config['TEMPLATES_FOLDER'], filename)
                })
        return jsonify({'status': 'success', 'templates': templates})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/run', methods=['POST'])
def run_template():
    try:
        data = request.json
        template = data.get('template', '')
        test_data = data.get('data', {})
        
        if not template:
            return jsonify({'error': 'No template provided'}), 400
        
        # Get the log count from the form
        # This should be passed from the frontend UI
        log_count = request.args.get('log_count', 1)
        
        # Add log_count to test_data
        if test_data is None:
            test_data = {}
        test_data['log_count'] = log_count
        
        # Process the template with sample data using Node.js
        result = process_liquid_template(template, test_data)
        
        return jsonify({'status': 'success', 'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 