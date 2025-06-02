# PySandbox

## Assignment Overview

**Instructions:**
- Build an API service that takes any Python script as input and returns the result of the script execution as output.
- The API should:
  - Accept a POST to `/execute` with a JSON body: `{ "script": "def main(): ..." }`
  - Execute the script and return the result of `main()` and any stdout (print output)
  - Only return the value from `main()` (must be JSON-serializable)
  - Throw an error if `main()` is missing or does not return JSON
  - Use Flask and nsjail for sandboxing
  - Allow access to basic libraries (os, pandas, numpy)
  - Be containerized (Docker), lightweight, and runnable with `docker run`
  - Be deployed to Google Cloud Run
  - Include a cURL example in the README
  - Provide basic input validation and robust security

**What was built:**
- A Flask API with a `/execute` endpoint that runs user-provided Python scripts and returns the result of `main()` and stdout.
- Scripts are sandboxed with nsjail when possible; if nsjail cannot be used (e.g., on Cloud Run), the API falls back to direct execution and includes a warning in the response.
- The service is containerized, supports pandas/numpy, and is deployed to Google Cloud Run.
- The README includes a cURL example, Cloud Run URL, and a clear explanation of nsjail limitations on Cloud Run.

---

## ⚠️ Important Note on Cloud Run and Linux Namespaces

> **Cloud Run's support for Linux namespaces (including `clone_newnet`) is not guaranteed and can change at any time.**

- Cloud Run is a fully managed platform, and Google may update the underlying kernel, container runtime, or security policies without notice.
- Features like network namespace isolation (`clone_newnet`) may work at one time and then become restricted or unavailable after a redeploy or platform update.
- This means that even if nsjail network isolation worked previously, it may suddenly stop working, as seen in recent testing (`unshare(CLONE_NEWNET): Operation not permitted`).
- Namespace support may also differ between deployments, as Cloud Run containers can land on different hosts with different kernel restrictions.
- **Do not rely on nsjail or Linux namespaces for security on Cloud Run.**
- For reliable sandboxing and namespace isolation, use a VM (e.g., GCP Compute Engine) or a privileged Kubernetes node (GKE).

---

## nsjail Namespaces on Cloud Run: What Works and What Doesn't

Through extensive testing, the following was found regarding nsjail namespaces on Google Cloud Run (gen2):

| Namespace         | Setting         | Result on Cloud Run (gen2)                                   | Effect/Notes                        |
|-------------------|----------------|--------------------------------------------------------------|-------------------------------------|
| clone_newnet      | true           | **Works:** Disables network access                           | Blocks DNS/network for sandboxed app|
| clone_newuser     | true           | **Fails:** Not permitted, nsjail error, fallback triggered   |                                     |
| clone_newpid      | true           | **Works:** No effect, script runs, no extra isolation        |                                     |
| clone_newns       | true           | **Fails:** nsjail error, fallback triggered (binary not found in ns) |                            |
| clone_newipc      | true           | **Works:** No effect, script runs, no extra isolation        |                                     |
| clone_newuts      | true           | **Works:** No effect, script runs, no extra isolation        |                                     |
| clone_newcgroup   | true           | **Works:** No effect, script runs, no extra isolation        |                                     |

**Key Takeaway:**
- Only `clone_newnet: true` (network namespace) provides a real security benefit and works reliably on Cloud Run. It disables all network access for the sandboxed process.
- All other namespaces either do not provide additional isolation, are not permitted, or cannot be combined due to Cloud Run's kernel restrictions.
- For true privilege or filesystem isolation, deploy on a VM or Kubernetes node with user and mount namespace support.

---

## 🚀 Cloud Run Service

- **URL:** https://pysandbox-1086809979020.us-central1.run.app

### Example cURL Requests

#### 1. Valid Script (should succeed)
```bash
curl -X POST https://pysandbox-1086809979020.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{"script": "def main():\n    print(\"Hello from main!\")\n    return {\"msg\": \"success\", \"value\": 42}\n"}'
```
**Expected:**
```json
{
  "result": {"msg": "success", "value": 42},
  "stdout": "Hello from main!",
  "warning": "nsjail could not be used; script ran without sandboxing"
}
```

#### 2. Missing `main()` Function (should error)
```bash
curl -X POST https://pysandbox-1086809979020.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{"script": "def not_main():\n    return 1\n"}'
```
**Expected:**
```json
{"error": "Script must contain a main() function."}
```

#### 3. `main()` Does Not Return JSON (should error)
```bash
curl -X POST https://pysandbox-1086809979020.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{"script": "def main():\n    return set([1,2,3])\n"}'
```
**Expected:**
```json
{"result": {"error": "Failed to parse main() return value: ..."}, "stdout": "", "warning": "nsjail could not be used; script ran without sandboxing"}
```

#### 4. Script With Exception in `main()`
```bash
curl -X POST https://pysandbox-1086809979020.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{"script": "def main():\n    raise Exception(\"fail!\")\n"}'
```
**Expected:**
```json
{"result": {"error": "fail!"}, "stdout": "", "warning": "nsjail could not be used; script ran without sandboxing"}
```

#### 5. Script With Only Print Statements
```bash
curl -X POST https://pysandbox-1086809979020.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{"script": "def main():\n    print(\"hi\")\n"}'
```
**Expected:**
```json
{"result": null, "stdout": "hi", "warning": "nsjail could not be used; script ran without sandboxing"}
```

#### 6. Script That Imports pandas/numpy
```bash
curl -X POST https://pysandbox-1086809979020.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{"script": "import pandas as pd\nimport numpy as np\ndef main():\n    df = pd.DataFrame({\"a\": [1,2]})\n    arr = np.array([1,2,3])\n    return {\"df_shape\": df.shape, \"arr_sum\": int(arr.sum())}\n"}'
```
**Expected:**
```json
{"result": {"df_shape": [2, 1], "arr_sum": 6}, "stdout": "", "warning": "nsjail could not be used; script ran without sandboxing"}
```

#### 7. Script That Tries to Access the Filesystem
```bash
curl -X POST https://pysandbox-1086809979020.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{"script": "def main():\n    try:\n        with open(\"/etc/passwd\") as f:\n            return {\"read\": f.read()}\n    except Exception as e:\n        return {\"error\": str(e)}\n"}'
```
**Expected:**
- On Cloud Run, the script will likely succeed in reading `/etc/passwd` (since nsjail is not active).
- On a real Linux VM with nsjail, this would be blocked.

#### 8. Script That Tries to Use the Network
```bash
curl -X POST https://pysandbox-1086809979020.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{"script": "import socket\ndef main():\n    try:\n        s = socket.socket()\n        s.connect((\"example.com\", 80))\n        return {\"network\": \"success\"}\n    except Exception as e:\n        return {\"error\": str(e)}\n"}'
```
**Expected:**
- On Cloud Run, outbound network may be allowed (unless restricted by VPC settings).
- On a real Linux VM with nsjail, this would be blocked.

#### 9. Script With Infinite Loop (should timeout)
```bash
curl -X POST https://pysandbox-1086809979020.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{"script": "def main():\n    while True: pass\n"}'
```
**Expected:**
```json
{"error": "Script execution timed out"}
```

#### 10. No Script Provided
```bash
curl -X POST https://pysandbox-1086809979020.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{}'
```
**Expected:**
```json
{"error": "No script provided"}
```

---

## Note on nsjail and Cloud Run

This service uses [nsjail](https://github.com/google/nsjail) for sandboxing untrusted Python code. **However, Google Cloud Run restricts access to certain Linux kernel features required by nsjail for full sandboxing.**

- On a real Linux VM (e.g., GCP Compute Engine, local Linux), nsjail provides strong isolation.
- On Cloud Run, attempts to use these features result in a fallback: the script is executed directly, and a warning is included in the response.
- This is a known limitation of Cloud Run and similar platforms.

#### How to test full nsjail functionality:
- Run the Docker container on a GCP Compute Engine VM or a local Linux machine.
- Or, deploy to a Kubernetes cluster (GKE) with the necessary privileges.

#### References:
- [Cloud Run Security Model](https://cloud.google.com/run/docs/container-contract#security)
- [nsjail GitHub Issues](https://github.com/google/nsjail/issues)

---

