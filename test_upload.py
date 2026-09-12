import requests
import json

url = "http://localhost:10001/api/upload-report"
files = {'file': ('test_report.pdf', b'dummy content', 'application/pdf')}
data = {'well_id': 'OIL-BAGHJAN-1'}

try:
    response = requests.post(url, files=files, data=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
