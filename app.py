import tempfile
import subprocess
import sys
import json
import os
from flask import Flask, request, jsonify

NSJAIL_PATH = '/usr/local/bin/nsjail'
NSJAIL_CFG = 'nsjail.cfg'

app = Flask(__name__)

@app.route('/execute', methods=['POST'])
def execute():
    data = request.get_json()
    script = data.get('script')
    if not script:
        return jsonify({'error': 'No script provided'}), 400
    if 'def main' not in script:
        return jsonify({'error': 'Script must contain a main() function.'}), 400

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

    # Build the command to run the script
    python_cmd = [sys.executable, tmp_file_path]
    use_nsjail = os.path.exists(NSJAIL_PATH) and os.path.exists(NSJAIL_CFG)
    if use_nsjail:
        cmd = [NSJAIL_PATH, '--config', NSJAIL_CFG, '--'] + python_cmd
    else:
        cmd = python_cmd

    warning = None
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=20
        )
        stdout = result.stdout
        stderr = result.stderr
        # Fallback: run without nsjail if nsjail fails for any reason
        if result.returncode != 0:
            warning = "nsjail could not be used; script ran without sandboxing"
            result = subprocess.run(
                python_cmd,
                capture_output=True,
                text=True,
                timeout=20
            )
            stdout = result.stdout
            stderr = result.stderr
            if result.returncode != 0:
                os.unlink(tmp_file_path)
                return jsonify({'error': 'Script execution failed (no nsjail fallback)', 'stderr': stderr}), 400
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

    response = {
        'result': main_result,
        'stdout': '\n'.join(output_lines)
    }
    if warning:
        response['warning'] = warning
    return jsonify(response)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=False)