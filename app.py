import tempfile
import subprocess
import sys
import json
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/execute', methods=['POST'])
def execute():
    data = request.get_json()
    script = data.get('script')
    if not script:
        return jsonify({'error': 'No script provided'}), 400

    # Append code to call main() and print its return value with a unique marker
    appended_code = ("\nimport json\n"
                     "if __name__ == '__main__':\n"
                     "    try:\n"
                     "        _main_result = main()\n"
                     "        print('___MAIN_RETURN___' + json.dumps(_main_result))\n"
                     "    except Exception as e:\n"
                     "        print('___MAIN_RETURN___' + json.dumps({'error': str(e)}))\n")
    full_script = script + appended_code

    # Write script to a temporary file
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as tmp_file:
        tmp_file.write(full_script)
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
            os.unlink(tmp_file_path)
            return jsonify({'error': 'Script execution failed', 'stderr': stderr}), 400
    except subprocess.TimeoutExpired:
        os.unlink(tmp_file_path)
        return jsonify({'error': 'Script execution timed out'}), 400
    except Exception as e:
        os.unlink(tmp_file_path)
        return jsonify({'error': str(e)}), 500

    # Parse stdout to extract main() return value
    main_result = None
    output_lines = []
    for line in stdout.splitlines():
        if line.startswith('___MAIN_RETURN___'):
            try:
                main_result = json.loads(line[len('___MAIN_RETURN___'):])
            except Exception as e:
                main_result = {'error': f'Failed to parse main() return value: {str(e)}'}
        else:
            output_lines.append(line)
    os.unlink(tmp_file_path)

    # If main_result is still None, main() was missing or not called
    if main_result is None:
        return jsonify({'error': 'main() function missing or did not return a value'}), 400

    return jsonify({
        'result': main_result,
        'stdout': '\n'.join(output_lines)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)