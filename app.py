from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os
import re
from werkzeug.utils import secure_filename
import uuid

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

def generate_liquid_template(json_data, company_name):
    # Get the title from the JSON data
    title = json_data[0]['runbook']['title'] if json_data else 'Untitled'
    
    # Extract variables from the detection rule
    rule = json_data[0]['detection_rule']['rule']
    variables = extract_variables_from_rule(rule)
    
    # Generate bullet points for each variable
    bullet_points = []
    for var in variables:
        bullet_points.append(f"  * **{var}:** `{{{{ log_entry.{var} }}}}`")
    
    bullet_points_str = "\n".join(bullet_points)
    
    template = f"""{{% assign log_entries = logs.log -%}}
{{% if log_entries.size == 1 -%}}
  {company_name} has detected {title}. As part of the investigation, {company_name} observed the following activity:

{bullet_points_str}

{{% else -%}}
  {company_name} has detected {title}. As part of the investigation, {company_name} observed multiple events:

  {{% for log_entry in log_entries %}}
{bullet_points_str}
  {{% endfor -%}}
{{% endif -%}}
"""
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
            
            company_name = request.form.get('company_name')
            
            # Generate Liquid template with the company name
            template = generate_liquid_template(json_data, company_name)
            
            # Get title from the first item in the JSON array
            title = json_data[0]['runbook']['title'] if json_data else 'Untitled'
            
            return jsonify({
                'status': 'success',
                'template': template,
                'title': title,
                'company_name': company_name
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
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

if __name__ == '__main__':
    app.run(debug=True) 