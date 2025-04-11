const fs = require('fs');
const { Liquid } = require('liquidjs');

// Get command line arguments
const templatePath = process.argv[2];
const dataPath = process.argv[3];
const outputPath = process.argv[4];

// Read template and data
const template = fs.readFileSync(templatePath, 'utf8');
let data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));

// Initialize Liquid engine with proper configuration
const engine = new Liquid({
    strictFilters: false,
    strictVariables: false,
    trimTagLeft: false,
    trimTagRight: false,
    trimOutputLeft: false,
    trimOutputRight: false
});

// Define some custom filters if needed
engine.registerFilter('strip', v => v ? v.toString().trim() : '');

// Process the template
try {
    engine.parseAndRender(template, data)
        .then(result => {
            // Write result to output file
            fs.writeFileSync(outputPath, result);
            console.log('Template processed successfully');
        })
        .catch(err => {
            console.error('Error processing template:', err.message);
            fs.writeFileSync(outputPath, 'Error processing template: ' + err.message);
            process.exit(1);
        });
} catch (err) {
    console.error('Fatal error in template processing:', err.message);
    fs.writeFileSync(outputPath, 'Fatal error in template processing: ' + err.message);
    process.exit(1);
} 