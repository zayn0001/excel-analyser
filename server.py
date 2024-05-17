import base64
import io
import json
import os
import openai
import pandas as pd
import requests
from deep_translator import GoogleTranslator
import uvicorn
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse
from typing_extensions import override
from dotenv import load_dotenv
import database
from functions import *
load_dotenv()
app = FastAPI()
    
client = openai.OpenAI()
@app.post("/ask_question/")
async def ask_question(file: UploadFile = File(...), question: str = Form(...), user: str = Form(...), restart: bool = Form(default=False)):

    question = GoogleTranslator(source='auto', target='en').translate(question) 
    
    file_stream = await get_file_stream(file)

    xfile = client.files.create(
    file=file_stream,
    purpose='assistants'
    )
    assistant = client.beta.assistants.create(
        instructions="You are a personal data analyst.",
        model="gpt-4-turbo",
        tools=[{"type": "code_interpreter"}],
        tool_resources={
            "code_interpreter": {
            "file_ids": [xfile.id]
            }
        }
    )
    threadid = database.get_user_thread(user)
    print(threadid)
    if threadid:
        if restart:
            thread = client.beta.threads.create()
            threadid = thread.id
            database.update_user_thread(user=user, threadid=threadid)

            run = client.beta.threads.runs.create_and_poll(
                thread_id=threadid,
                assistant_id=assistant.id,
                instructions="You have been provided a csv file of which the first row corresponds to its columns. \
                            When asked a question related to the data provided, write and run code to answer the question. \
                            Do not ask any confirming questions. Assume all that is necessary. \
                            Do not mention anything insinuating that a file has been uploaded. Answer the following question: " + question,
            )
        else:
            run = client.beta.threads.runs.create_and_poll(
                thread_id=threadid,
                assistant_id=assistant.id,
                instructions=question
            )

    else:
        thread = client.beta.threads.create()
        threadid = thread.id
        database.create_user_thread(user=user, threadid=threadid)

        run = client.beta.threads.runs.create_and_poll(
            thread_id=threadid,
            assistant_id=assistant.id,
            instructions="You have been provided a csv file of which the first row corresponds to its columns. \
                        When asked a question related to the data provided, write and run code to answer the question. \
                        Do not ask any confirming questions. Assume all that is necessary. \
                        Do not mention anything insinuating that a file has been uploaded. Answer the following question: " + question,
        )

    if run.status == 'completed': 

        messages = client.beta.threads.messages.list(
            thread_id=threadid,
            run_id=run.id
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
            dfdict = df.to_dict(orient="records")
    
            return JSONResponse(
                content={"json":dfdict}
            )


        elif contents[0].type == "text":
            return JSONResponse(
                content={
                    "text": contents[0].text.value
                }
            )
        

@app.post("/create_product/")
async def ask_question(question: str = Form(...)):
    assistant = client.beta.assistants.create(
        instructions="You are a json formatter. You will be provided with text of details of a product and you have to provide the formatted json of it",
        model="gpt-4-turbo",
        tools=[{"type": "code_interpreter"}]
    )
    thread = client.beta.threads.create()

    run = client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=assistant.id,
                instructions= "You are a json formatter. You will be provided with text of details of a product and you have to provide the formatted json of it. they should all be in double quotes according to json structure\
                     in the creation of products there are some mandatory fields, such as the name, category, \
                    brand, VAT and type of product. The different types are  (simple, size and colours, formats, batches). if the product is type size and colors, sizes and colors must be added to the mandatory fields \
                        if the product type is formats, you must add the formats as a mandatory field. \
                            if the product type is batches, you must add the batches as a mandatory field. if the necessary values for a specifc type is not mentioned, let me know. \
                                 Example:\n \
                                    Input: Can you create a product with formats, with the title PERFUME, PERFUMES FOR MEN category, CHANEL brand, VAT 22, price €100, formats 50ml,100ml \n \
                                    Output: { \
                                    name: 'PERFUME', \
                                    type: 'formats' \
                                    category: 'PERFUMES FOR MEN',\
                                    brand: 'CHANEL',\
                                    VAT: 22,\
                                    price: 100,\
                                    formats; ['50ml','100ml']\
                                     \
                                    } " + question
            )
    

    if run.status == 'completed': 

        messages = client.beta.threads.messages.list(
            thread_id=thread.id,
            run_id=run.id
        )
        
        contents = messages.data[0].content
        msg = contents[0].text.value
        if msg[0]=="{" or msg[0]=="[":
            return JSONResponse(content=json.loads(contents[0].text.value), status_code=200)
        else: 
            return JSONResponse(status_code=404, content=msg)
        

@app.post("/create_brand/")
async def ask_question(question: str = Form(...)):
    assistant = client.beta.assistants.create(
        instructions="You are a json formatter. You will be provided with text of details of a brand and you have to provide the formatted json of it",
        model="gpt-4-turbo",
        tools=[{"type": "code_interpreter"}]
    )
    thread = client.beta.threads.create()

    run = client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=assistant.id,
                instructions= "You are a json formatter. You will be provided with name of a brand or a list of brands and you have to provide the formatted json of it. a brand also only one attribute, that is, name. they should all be in double quotes according to json structure. numbers should be in number format.  \
                                 Example:\n \
                                    Input: Can you create a brand with name NIKE \n \
                                    Output: { \
                                    \"name\": 'NIKE', \
                                     \
                                    } \n \
                                    Example:\n \
                                    Input: Can you create a list of these brands : NIKE,ADIDAS \n \
                                    Output: [ { \n \
                                    name:'NIKE' \n \
                                    }, \n \
                                    { \n \
                                     name: 'ADIDAS'     \n \
                                    }\n " + question
            )
    

    if run.status == 'completed': 

        messages = client.beta.threads.messages.list(
            thread_id=thread.id,
            run_id=run.id
        )
        
        contents = messages.data[0].content
        msg = contents[0].text.value

        msg = msg.replace("```json", "").replace("```","")
        if msg[0]=="{" or msg[0]=="[" :
            return JSONResponse(content=json.loads(contents[0].text.value), status_code=200)
        else: 
            return JSONResponse(status_code=404, content=msg)
        


@app.post("/create_furnisher/")
async def ask_question(question: str = Form(...)):
    assistant = client.beta.assistants.create(
        instructions="You are a json formatter. You will be provided with text of details of a furnisher and you have to provide the formatted json of it",
        model="gpt-4-turbo",
        tools=[{"type": "code_interpreter"}]
    )
    thread = client.beta.threads.create()

    run = client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=assistant.id,
                instructions= "You are a json formatter. You will be provided with name of a furnisher or a list of furnishers and you have to provide the formatted json of it. a furnisher has the following attributes: name, surname, company, address, city, vat_number, tax_id_code, country. they should all be in double quotes according to json structure. \
                   if any field is missing or not proper from the input, let me know. numbers should be in number format\
                                 Example:\n \
                                    Input: Can you create a furnisher with name : TEST ,surname testtest, company TEST PROVA, vat number 12345678901,address street 10, city Rome, country Italy, tax id 423235 \n \
                                    Output: { \
                                    \"name\": 'TEST', \
                                    \"surname\": 'testtest', \
                                    \"company\": 'TEST PROVA', \
                                    \"vat_number\": 12345678901, \
                                    \"address\": 'street 10', \
                                    \"city\": 'Rome', \
                                    \"country\": 'Italy', \
                                    \"tax_id_code\": 423235, \
                                     \
                                    } \n \
                                    " + question
            )
    

    if run.status == 'completed': 

        messages = client.beta.threads.messages.list(
            thread_id=thread.id,
            run_id=run.id
        )
        
        contents = messages.data[0].content
        msg = contents[0].text.value

        msg = msg.replace("```json", "").replace("```","")
        if msg[0]=="{" or msg[0]=="[" :
            return JSONResponse(content=json.loads(contents[0].text.value), status_code=200)
        else: 
            return JSONResponse(status_code=404, content=msg)



@app.post("/create_customer/")
async def ask_question(question: str = Form(...)):
    assistant = client.beta.assistants.create(
        instructions="You are a json formatter. You will be provided with text of details of a customer and you have to provide the formatted json of it",
        model="gpt-4-turbo",
        tools=[{"type": "code_interpreter"}]
    )
    thread = client.beta.threads.create()

    run = client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=assistant.id,
                instructions= "You are a json formatter. You will be provided with name of a customer or a list of customers and you have to provide the formatted json of it. a customer has the following attributes: name, surname, company, address, city, vat_number, tax_id_code, country. they should all be in double quotes according to json structure. \
                   if any field is missing or not proper from the input, let me know. numbers should be in number format\
                                 Example:\n \
                                    Input: Can you create a customer with name : TEST ,surname testtest, company TEST PROVA, vat number 12345678901,address street 10, city Rome, country Italy, tax id 423235 \n \
                                    Output: { \
                                    \"name\": 'TEST', \
                                    \"surname\": 'testtest', \
                                    \"company\": 'TEST PROVA', \
                                    \"vat_number\": 12345678901, \
                                    \"address\": 'street 10', \
                                    \"city\": 'Rome', \
                                    \"country\": 'Italy', \
                                    \"tax_id_code\": 423235, \
                                     \
                                    } \n \
                                    " + question
            )
    

    if run.status == 'completed': 

        messages = client.beta.threads.messages.list(
            thread_id=thread.id,
            run_id=run.id
        )
        
        contents = messages.data[0].content
        msg = contents[0].text.value

        msg = msg.replace("```json", "").replace("```","")
        if msg[0]=="{" or msg[0]=="[" :
            return JSONResponse(content=json.loads(contents[0].text.value), status_code=200)
        else: 
            return JSONResponse(status_code=404, content=msg)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
