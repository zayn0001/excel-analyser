import base64
import io
import json
import os
import openai
import pandas as pd
import requests
from deep_translator import GoogleTranslator
import uvicorn
import datetime
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse
from openai import AssistantEventHandler
from typing_extensions import override
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

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
    
"""
class EventHandler(AssistantEventHandler):    
  @override
  def on_text_created(self, text) -> None:
    print(f"\nassistant > ", end="", flush=True)
      
  @override
  def on_text_delta(self, delta, snapshot):
    print(delta.value, end="", flush=True)
      
  def on_tool_call_created(self, tool_call):
    print(f"\nassistant > {tool_call.type}\n", flush=True)
  
  def on_tool_call_delta(self, delta, snapshot):
    if delta.type == 'code_interpreter':
      if delta.code_interpreter.input:
        print(delta.code_interpreter.input, end="", flush=True)
      if delta.code_interpreter.outputs:
        print(f"\n\noutput >", flush=True)
        for output in delta.code_interpreter.outputs:
          if output.type == "logs":
            print(f"\n{output.logs}", flush=True)
"""

global thread
global lastrun
global assistant
global filename
global timenow
timenow = datetime.datetime.now()
filename = ""

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

client = openai.OpenAI()
@app.post("/ask_question/")
async def ask_question(file: UploadFile = File(...), question: str = Form(...)):

    question = GoogleTranslator(source='auto', target='en').translate(question) 

    now = datetime.datetime.now()
    global thread
    global timenow
    global assistant
    global filename
    diff = now - timenow
    if file.filename!=filename or diff.total_seconds() > 120 :
        timenow = now
        file_stream = await get_file_stream(file)
        xfile = client.files.create(
        file=file_stream,
        purpose='assistants'
        )
        assistant = client.beta.assistants.create(
            instructions="You are a personal data analyst. \
                ",
            model="gpt-4-turbo",
            tools=[{"type": "code_interpreter"}],
            tool_resources={
                "code_interpreter": {
                "file_ids": [xfile.id]
                }
            }
        )
        thread = client.beta.threads.create()
        filename = file.filename

    run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id,
    assistant_id=assistant.id,
    instructions="You have been provided a csv file of which the first row corresponds to its columns. \
                When asked a question related to the data provided, write and run code to answer the question. \
                Do not ask any confirming questions. Assume all that is necessary. \
                Do not mention anything insinuating that a file has been uploaded. Answer the following question: " + question,
    )

    """
    with client.beta.threads.runs.stream(
        thread_id=thread.id,
        assistant_id=assistant.id,
        instructions=question,
        event_handler=EventHandler(),
    ) as stream:
        stream.until_done()
    """


    if run.status == 'completed': 

        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        
        contents = messages.data[0].content
        print(contents)

            
        if contents[0].type == "image_file":
           
            image_file_id = contents[0].image_file.file_id
            text = contents[1].text.value
            
            image_data = client.files.content(image_file_id)
            image_data_bytes = image_data.read()
            image_base64 = base64.b64encode(image_data_bytes).decode('utf-8')
            image_url = upload_image_to_imgbb(image_base64)
            
            try:
                return JSONResponse(
                    content={
                        "image": image_url,
                        "text": text
                    }
                )
            except:
                return contents
            
        elif contents[0].text.annotations:
            csvfileid = contents[0].text.annotations[0].file_path.file_id
            filecont =  client.files.content(csvfileid)
            data = filecont.read()  
            csv_data_str = data.decode('utf-8') 
            df = pd.read_csv(io.StringIO(csv_data_str))
            #excel_filename = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False).name
            #df.to_excel(excel_filename, index=False)
            dfdict = df.to_dict(orient="records")
            #url = 'https://tmpfiles.org/api/v1/upload'
            #files = {'file': open(excel_filename, 'rb')}
            #response = requests.post(url, files=files)
            
            #file_info = response.json()
            #downloadurl = "https://tmpfiles.org/dl/"+ file_info["data"]["url"].split("https://tmpfiles.org/")[1]
            #print(file_info)
            return JSONResponse(
                content={"json":dfdict}
            )


        elif contents[0].type == "text":
            return JSONResponse(
                content={
                    "text": contents[0].text.value
                }
            )

        

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
