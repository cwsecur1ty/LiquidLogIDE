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
- **Event ID**: {{ log_entries[0].EventType }}
- **Target Object**: {{ log_entries[0].TargetObject }}
- **Subject User**: {{ log_entries[0].SubjectUserName }}
- **Subject SID**: {{ log_entries[0].SubjectUserSid }}

## Details
- **Company**: {0}
- **Event Time**: {{ log_entries[0].EventTime }}
- **Client IP**: {{ log_entries[0].client_ip }}
- **Target User**: {{ log_entries[0].TargetUserName }}
- **Target Domain**: {{ log_entries[0].TargetDomainName }}
- **Subject User**: {{ log_entries[0].SubjectUserName }}
- **Subject SID**: {{ log_entries[0].SubjectUserSid }}
- **Event Type**: {{ log_entries[0].EventType }}
- **Target Object**: {{ log_entries[0].TargetObject }}

## Outcome Processing
{% if log_entries[0].EventType == "4657" %}
- **Action**: Registry key value modified
- **Key**: {{ log_entries[0].TargetObject }}
- **Value**: {{ log_entries[0].NewValue }}
{% endif %}

## Additional Context
- **Process ID**: {{ log_entries[0].ProcessId }}
- **Thread ID**: {{ log_entries[0].ThreadId }}
- **Computer**: {{ log_entries[0].Computer }}
""".format(company_name)
    else:
        return """{% assign log_entries = logs.log %}
# Multiple Events

## Overview
- **Company**: {0}
- **Number of Events**: {1}

## Events
{% for log_entry in log_entries %}
### Event {{ forloop.index }}
- **Event ID**: {{ log_entry.EventType }}
- **Target Object**: {{ log_entry.TargetObject }}
- **Subject User**: {{ log_entry.SubjectUserName }}
- **Subject SID**: {{ log_entry.SubjectUserSid }}

#### Details
- **Event Time**: {{ log_entry.EventTime }}
- **Client IP**: {{ log_entry.client_ip }}
- **Target User**: {{ log_entry.TargetUserName }}
- **Target Domain**: {{ log_entry.TargetDomainName }}
- **Subject User**: {{ log_entry.SubjectUserName }}
- **Subject SID**: {{ log_entry.SubjectUserSid }}
- **Event Type**: {{ log_entry.EventType }}
- **Target Object**: {{ log_entry.TargetObject }}

#### Outcome Processing
{% if log_entry.EventType == "4657" %}
- **Action**: Registry key value modified
- **Key**: {{ log_entry.TargetObject }}
- **Value**: {{ log_entry.NewValue }}
{% endif %}

#### Additional Context
- **Process ID**: {{ log_entry.ProcessId }}
- **Thread ID**: {{ log_entry.ThreadId }}
- **Computer**: {{ log_entry.Computer }}
{% endfor %}
""".format(company_name, num_entries)

def process_liquid_template(template, data):
    """Process data and create a template based on the JSON structure"""
    try:
        # Get the log data from the appropriate structure
        if 'logs' in data and 'log' in data['logs']:
            logs = data['logs']['log']
        else:
            # If the structure is not as expected, use the data as is
            logs = data if isinstance(data, list) else [data]
        
        # Determine if we have single or multiple entries
        if len(logs) == 1:
            # Single entry template
            log = logs[0]
            output = f"# {log.get('title', 'Untitled')} - {log.get('logsource', {}).get('product', '')}\n\n"
            
            output += "## Overview\n"
            output += f"- **Event ID**: {log.get('id', '')}\n"
            output += f"- **Target Object**: {log.get('description', '')}\n"
            output += f"- **Subject User**: {log.get('author', '')}\n"
            output += f"- **Subject SID**: {log.get('references', [])}\n\n"
            
            output += "## Details\n"
            
            # Expand all fields that exist in the log
            for key, value in log.items():
                # Skip fields already included in overview or that are complex objects
                if key in ['id', 'description', 'author', 'references'] or isinstance(value, (dict, list)):
                    continue
                
                output += f"- **{key}**: {value}\n"
            
            # If there are detection rules, include them
            if 'detection' in log:
                output += "\n## Detection Rules\n"
                if isinstance(log['detection'], dict):
                    for rule_name, rule_value in log['detection'].items():
                        if isinstance(rule_value, dict):
                            output += f"- **{rule_name}**:\n"
                            for field, criteria in rule_value.items():
                                if isinstance(criteria, list):
                                    criteria_str = ", ".join([f"`{c}`" for c in criteria])
                                    output += f"  - {field}: {criteria_str}\n"
                                else:
                                    output += f"  - {field}: `{criteria}`\n"
                        elif isinstance(rule_value, list):
                            criteria_str = ", ".join([f"`{c}`" for c in rule_value])
                            output += f"- **{rule_name}**: {criteria_str}\n"
                        else:
                            output += f"- **{rule_name}**: `{rule_value}`\n"
        else:
            # Multiple entries template
            output = "# Multiple Events\n\n"
            output += "## Overview\n"
            output += f"- **Number of Events**: {len(logs)}\n\n"
            
            # Generate entry for each log
            for i, log in enumerate(logs):
                output += f"## Event {i+1}: {log.get('title', 'Untitled')}\n\n"
                
                # Basic information
                output += f"- **Event ID**: {log.get('id', '')}\n"
                output += f"- **Target Object**: {log.get('description', '')}\n"
                output += f"- **Subject User**: {log.get('author', '')}\n"
                
                # Add additional details
                output += "\n### Details\n"
                
                # Expand all fields that exist in the log
                for key, value in log.items():
                    # Skip fields already included or that are complex objects
                    if key in ['id', 'description', 'author'] or isinstance(value, (dict, list)):
                        continue
                    
                    output += f"- **{key}**: {value}\n"
                
                # If there are detection rules, include them
                if 'detection' in log:
                    output += "\n### Detection Rules\n"
                    if isinstance(log['detection'], dict):
                        for rule_name, rule_value in log['detection'].items():
                            if isinstance(rule_value, dict):
                                output += f"- **{rule_name}**:\n"
                                for field, criteria in rule_value.items():
                                    if isinstance(criteria, list):
                                        criteria_str = ", ".join([f"`{c}`" for c in criteria])
                                        output += f"  - {field}: {criteria_str}\n"
                                    else:
                                        output += f"  - {field}: `{criteria}`\n"
                            elif isinstance(rule_value, list):
                                criteria_str = ", ".join([f"`{c}`" for c in rule_value])
                                output += f"- **{rule_name}**: {criteria_str}\n"
                            else:
                                output += f"- **{rule_name}**: `{rule_value}`\n"
                                
                output += "\n"
        
        return output
    except Exception as e:
        print(f"Error processing data: {str(e)}")
        return f"Error processing data: {str(e)}"

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
    
    # Add the field outputs for single event
    for field in detection_fields:
        template += f'  * **{field}:** `{{{{ log_entries[0].{field} }}}}`\n'
    
    # Add the multiple events section
    template += '\n{% else -%}\n'
    template += f'  {company_name} has detected {title}. As part of the investigation, {company_name} observed multiple events:\n\n'
    template += '  {% for log_entry in log_entries %}\n'
    
    # Add the field outputs for multiple events
    for field in detection_fields:
        template += f'  * **{field}:** `{{{{ log_entry.{field} }}}}`\n'
    
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
        
        if not template:
            return jsonify({'error': 'No template provided'}), 400
        
        # Just display the template as-is
        result = "Template Preview (not processed):\n\n" + template
        
        return jsonify({'status': 'success', 'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 