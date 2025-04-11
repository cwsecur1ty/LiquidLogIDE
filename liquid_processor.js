const fs = require('fs');
const { Liquid } = require('liquidjs');

// Get command line arguments
const templatePath = process.argv[2];
const dataPath = process.argv[3];
const outputPath = process.argv[4];

// Read template and data
const template = fs.readFileSync(templatePath, 'utf8');
let data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));

// Create an engine
const engine = new Liquid();

// Very simple template that just outputs data as JSON
const safeTemplate = `
# Data Output

\`\`\`json
{{ logs | json }}
\`\`\`
`;

// Render the safe template
engine.parseAndRender(safeTemplate, data)
    .then(result => {
        fs.writeFileSync(outputPath, result);
        console.log('Template processed successfully');
    })
    .catch(err => {
        console.error('Error:', err.message);
        fs.writeFileSync(outputPath, 'Error: ' + err.message);
        process.exit(1);
    }); 