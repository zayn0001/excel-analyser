import base64
import json
from dotenv import load_dotenv
import requests
import os
import io
import pandas as pd
import re
import openai
load_dotenv()


def get_messages(thread_id):
    client = openai.OpenAI()
    messages = client.beta.threads.messages.list(
                thread_id=thread_id,
            )

    mymess = []
    for message in messages:
        role = message.role
        contents = message.content

        if contents[0].type == "image_file":
            
            image_file_id = contents[0].image_file.file_id
            text = contents[1].text.value
            
            image_data = client.files.content(image_file_id)
            image_data_bytes = image_data.read()
            image_base64 = base64.b64encode(image_data_bytes).decode('utf-8')
            image_url = upload_image_to_imgbb(image_base64)
            
            
            content={
                "image": image_url,
                "text": text
            }
            
            
            
        elif contents[0].text.annotations:
            csvfileid = contents[0].text.annotations[0].file_path.file_id
            filecont =  client.files.content(csvfileid)
            data = filecont.read()  
            csv_data_str = data.decode('utf-8') 
            df = pd.read_csv(io.StringIO(csv_data_str))
            dfdict = df.to_dict(orient="records")

            
            content={"json":dfdict}
            


        elif contents[0].type == "text":
            
            content={
                "text": contents[0].text.value
            }
        mymess.append({"role":role, "content":content})
    return mymess
            

def convert_str_to_json(json_string):
  match = re.search(r'\{(.*)\}', json_string, re.DOTALL)
  if match:
      extracted_content = '{' + match.group(1) + '}'
      json_object = json.loads(extracted_content)
      return json_object
  else:
      return json_string
      
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
