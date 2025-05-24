import tempfile
import subprocess
import sys
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/execute', methods=['POST'])
def execute():
    data = request.get_json()
    script = data.get('script')
    if not script:
        return jsonify({'error': 'No script provided'}), 400

    # Write script to a temporary file
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as tmp_file:
        tmp_file.write(script)
        tmp_file_path = tmp_file.name

    # Execute the script in a subprocess and capture stdout
    try:
        result = subprocess.run(
            [sys.executable, tmp_file_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        stdout = result.stdout
        stderr = result.stderr
        if result.returncode != 0:
            return jsonify({'error': 'Script execution failed', 'stderr': stderr}), 400
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Script execution timed out'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({
        'result': None,  # We'll extract main() return value later
        'stdout': stdout
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)