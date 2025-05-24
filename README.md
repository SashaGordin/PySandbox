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

## 🚀 Cloud Run Service

- **URL:** https://pysandbox-1086809979020.us-central1.run.app

### Example cURL Request

```bash
curl -X POST https://pysandbox-1086809979020.us-central1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{"script": "def main():\n    print(\"Hello from main!\")\n    return {\"msg\": \"success\", \"value\": 42}\n"}'
```

### Note on nsjail and Cloud Run

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

