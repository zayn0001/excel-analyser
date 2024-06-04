import openai
from deep_translator import GoogleTranslator
import uvicorn
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import database
from functions import *
import constants
load_dotenv()

app = FastAPI()    
client = openai.OpenAI()


@app.post("/get_email")
async def ask_question(request: str = Form(...)):
    thread = client.beta.threads.create()
    assistant = client.beta.assistants.create(
            instructions="You are an email generator",
            model="gpt-4o")
    run = client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=assistant.id,
                instructions="You will be provided with a request to compose an email. the email should be structured in json format like {\"subject\":\"Request for leave\", \"content\":\"...\"}. Do not add an email signature or a best regards. Only include the body. Do not answer with anything but the json. The request is the following: " + request,
    )
    if run.status == 'completed': 

        messages = client.beta.threads.messages.list(
            thread_id=thread.id,
            run_id=run.id
        )
        contents = messages.data[0].content
        print(contents[0].text.value)
        msg = get_json(contents)
        return JSONResponse(content=msg, status_code=200)
    


@app.post("/get_whatsapp")
async def ask_question(request: str = Form(...)):
    thread = client.beta.threads.create()
    assistant = client.beta.assistants.create(
            instructions="You are a whatsapp message generator",
            model="gpt-4o")
    run = client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=assistant.id,
                instructions="You will be provided with a request to compose a Whatsapp message. the Whatsapp message should be structured in json format like {\"content\":\"...\"}. Do not add a signature or a best regards. Only include the body. Use appropriate bold and italics formats. Do not answer with anything but the json. The request is the following: " + request,
    )
    if run.status == 'completed': 

        messages = client.beta.threads.messages.list(
            thread_id=thread.id,
            run_id=run.id
        )
        contents = messages.data[0].content
        print(contents[0].text.value)
        msg = get_json(contents)
        return JSONResponse(content=msg, status_code=200)


@app.post("/add_file")
async def ask_question(user: str = Form(...), file: UploadFile = File(...)):
    file_stream = await get_file_stream(file)
    xfile = client.files.create(file=file_stream,purpose='assistants')
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
    database.add_user_file(user, file.filename,assistant.id)
    return JSONResponse(content={"filename":file.filename})

@app.post("/get_files")
async def ask_question(user: str = Form(...)):
    
    files = database.get_all_filenames(user)
    return JSONResponse(content={"files":files})

@app.post("/get_history")
async def ask_question(user: str = Form(...)):
    return database.get_user_history(user)


@app.post("/ask_question")
async def ask_question(assistantid: str = Form(None), question: str = Form(...), user: str = Form(...), restart: bool = Form(default=False)):

    question = GoogleTranslator(source='auto', target='en').translate(question)
    print("hi")
    if assistantid:
        pass
    else:
        dataset = get_dataset_name(question=question)
        apiurl = constants.DATASETS[dataset]
        filestream = get_file_stream_from_api(apiurl)
        xfile = client.files.create(file=filestream,purpose='assistants')
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
        assistantid = assistant.id




    threadid = database.get_user_thread(user)

    if threadid:
        if restart:
            thread = client.beta.threads.create()
            threadid = thread.id
            database.update_user_thread(user=user, threadid=threadid)

            run = client.beta.threads.runs.create_and_poll(
                thread_id=threadid,
                assistant_id=assistantid,
                instructions="You have been provided a csv file of which the first row corresponds to its columns. \
                            When asked a question related to the data provided, write and run code to answer the question. \
                            Do not ask any confirming questions. Assume all that is necessary. \
                            Do not mention anything insinuating that a file has been uploaded. Answer the following question: " + question,
            )
        else:
            run = client.beta.threads.runs.create_and_poll(
                thread_id=threadid,
                assistant_id=assistantid,
                instructions=question
            )

    else:
        thread = client.beta.threads.create()
        threadid = thread.id
        database.create_user_thread(user=user, threadid=threadid)

        run = client.beta.threads.runs.create_and_poll(
            thread_id=threadid,
            assistant_id=assistantid,
            instructions="You have been provided a csv file of which the first row corresponds to its columns. \
                        When asked a question related to the data provided, write and run code to answer the question. \
                        Do not ask any confirming questions. Assume all that is necessary. \
                        Do not mention anything insinuating that a file has been uploaded. Answer the following question: " + question,
        )

    if run.status == 'completed': 

        messages = client.beta.threads.messages.list(thread_id=threadid,run_id=run.id)
        contents = messages.data[0].content
            
        if contents[0].type == "image_file":
            image_url, text = get_image_url_and_text(contents)
            database.convo(user,question,{"image":image_url, "text":text})
            return JSONResponse(content={"image":image_url, "text":text})
            
        elif contents[0].text.annotations:
            dfdict = get_json_of_file(contents)
            database.convo(user,question,{"json":dfdict})
            return JSONResponse(content={"json":dfdict})
        
        elif contents[0].type == "text":
            database.convo(user,question,{"text": contents[0].text.value})
            return JSONResponse(content={"text": contents[0].text.value})
        




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
                instructions= "You are a json formatter. You will be provided with text of details of a product and you have to provide the formatted json of it. they should all be in double quotes according to json structure \
                     in the creation of products there are some mandatory fields, such as the name, category, brand, VAT and type of product. The different types are  (simple, variety, formats, batches). \
                     if the product is type variety, sizes and colors must be added to the mandatory fields. \
                        if the product type is formats, you must add the formats as a mandatory field. \
                            if the product type is batches, you must add the batches as a mandatory field. \
                                if the necessary values for a specific type is not mentioned, let me know. \
                                for the variety product, if only sizes or colors is provided let me know. \
                                even if i say it is a simple product and give formats or sizes and colors, make it formats type and variety type respectively. \
                                give more preference to the data provided and less to the type mentioned. \
                                any other combination other than the ones mentioned are not allowed.\
                                IF I MENTION SIZES I HAVE TO MENTION COLORS OR IT IS INVALID AND VICE VERSA.\
                                forgive small spelling mistakes. \
                                Whenever an invalid input is given, reply it is invalid and give reason in a single sentence. if not invalid reply in the following manner.  \
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
        msg = get_json(contents)
        return JSONResponse(content=msg, status_code=200)
        



        

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
        msg = get_json(contents)
        return JSONResponse(content=msg, status_code=200)
        
        


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
        msg = get_json(contents)
        return JSONResponse(content=msg, status_code=200)



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
        msg = get_json(contents)
        return JSONResponse(content=msg, status_code=200)





if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
