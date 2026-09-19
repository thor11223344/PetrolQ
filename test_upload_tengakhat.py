import requests
import json

url = "http://localhost:8000/api/upload-report"
pdf_path = "sample_reports/OIL_Tengakhat_DDR_Well_01.pdf"

try:
    with open(pdf_path, "rb") as f:
        files = {'file': ('OIL_Tengakhat_DDR_Well_01.pdf', f, 'application/pdf')}
        data = {'well_id': 'OIL-TENGAKHAT-1'}
        response = requests.post(url, files=files, data=data)
        
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
