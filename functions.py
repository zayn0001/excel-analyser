import json
import requests
import os
import io
import pandas as pd

def upload_image_to_imgbb(images_bytes):
    url = "https://api.imgbb.com/1/upload"
    
    payload = {
        "key": os.environ.get("IMGBB_KEY"),
        "image": images_bytes,
        "expiration":600
    }
    
    response = requests.post(url, payload)
    result = json.loads(response.text)
    url = result["data"]["url"]
    print(url)
    return url

async def get_file_stream(file):
    print(file.filename)
    if file.filename.endswith(".xlsx"):
        print(".xlsx")
        file_content = await file.read()
        df = pd.read_excel(io.BytesIO(file_content), sheet_name=0)
        csv_string = df.to_csv(index=False)
        csv_bytes = csv_string.encode()
        file_stream = io.BytesIO(csv_bytes)
    
    if file.filename.endswith(".csv"):
        print(".csv")
        file_content = await file.read()
        file_stream = io.BytesIO(file_content)

    if file.filename.endswith(".json"):
        print(".json")
        file_content = await file.read()
        data = json.loads(file_content)
        df = pd.DataFrame(data)
        csv_data = df.to_csv(index=False)
        csv_bytes = csv_data.encode()
        file_stream = io.BytesIO(csv_bytes)

    return file_stream
