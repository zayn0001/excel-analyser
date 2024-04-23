import base64
import io
import json

import openai
import pandas as pd
import requests
import uvicorn
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse

from openai import AssistantEventHandler
from typing_extensions import override

app = FastAPI()
# First, we create a EventHandler class to define
# how we want to handle the events in the response stream.
def upload_image_to_imgbb(images_bytes):
    api_key = "aa0696eab1a460991ba67d2ed95e2602"
    url = "https://api.imgbb.com/1/upload"
    
    payload = {
        "key": api_key,
        "image": images_bytes,
        "expiration":600
    }
    
    response = requests.post(url, payload)
    result = json.loads(response.text)
    url = result["data"]["url"]
    print(url)
    return url
    

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


@app.post("/ask_question/")
async def ask_question(file: UploadFile = File(...), question: str = Form(...)):

    #excel to bytes
    file_content = await file.read()
    file_stream = io.BytesIO(file_content)
    df = pd.read_excel(io.BytesIO(file_content), sheet_name=0)
    csv_string = df.to_csv(index=False)
    csv_bytes = csv_string.encode()
    file_stream = io.BytesIO(csv_bytes)


    client = openai.OpenAI(api_key="sk-proj-nfDjEgAqwCfb4k8YKQ6tT3BlbkFJfIaNyUlnkPlepCtjZ0vG")

    xfile = client.files.create(
    file=file_stream,
    purpose='assistants'
    )

    assistant = client.beta.assistants.create(
        instructions="You are a personal data analyst. You have been provided an xlsx file of which the first row corresponds to its columns. When asked a question related to the data provided, write and run code to answer the question.",
        model="gpt-4-turbo",
        tools=[{"type": "code_interpreter"}],
        tool_resources={
            "code_interpreter": {
            "file_ids": [xfile.id]
            }
        }
    )

    thread = client.beta.threads.create()

    run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id,
    assistant_id=assistant.id,
    instructions=question,
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
            
        if contents[0].type == "text":
            return JSONResponse(
                content={
                    "text": contents[0].text.value
                }
            )

        

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
