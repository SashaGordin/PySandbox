# PySandbox
Here is a simple task that should not take more than 1-2 hours. This is not a timed task, take
your time. Just as a benchmark.
Business context: You are building a service that enables customers to execute arbitrary
python code on a cloud server. The user sends a python script and the execution result of
the main() function gets returned.
Goal: build an API service that takes any python script as input and returns the result of the
script execution as output.
Details: When sending a POST request to the /execute endpoint with a multiline JSON as
request body {"script": "def main(): ..."}, the service should execute the python script and
return the result of the function main(). Print statements in the stdout should not be included
in the return, only the return statement of the main() function should be captured. Therefore,
you should expect a function main() that returns a JSON. If the file does not contain a
function main() or does not return a JSON, an error must be thrown.
The service is a simple docker image exposing port 8080. The API is deployed on Google
Cloud Run as an API.
The API response after script execution should look as follows:
{
“result”: ..., # return of the main() function
“stdout”: ... # the stdout of the script execution
}
Criteria:
1. The docker image should not be too heavy
2. only a docker run command is necessary to run the service locally
3. The ReadMe documentation should contain an example cURL request with the
cloud run URL embedded to make it easy to try out.
4. There should be basic input validation
5. The execution of the python script should be safe, meaning that it is robust to any
malicious user-defined scripts that might be executed.
6. Basic libraries like os, pandas and numpy should be accessible by the script
7. You should use Flask and nsjail.
Hints: you can have some inspiration at:
1. https://nsjail.dev/
2. https://github.com/google/nsjail
3. https://github.com/windmill-labs/windmill/blob/main/backend/windmill-worker/nsjail/
download.py.config.proto

When submitting the take home challenge, please indicate
1. Github repository URL (public or shared with RubenB1)

1

2. The Google Cloud Run service URL
3. As a benchmark, an approximation of how long it did take you to complete the
challenge (this makes no difference in our appreciation).