from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


def get_user_thread(user):
    # MongoDB connection URI
    uri = "mongodb+srv://mishal0404:mishal2003@mishal0404.35lsnon.mongodb.net/?retryWrites=true&w=majority&appName=mishal0404"
    
    # Connect to MongoDB
    client = MongoClient(uri, server_api=ServerApi('1'))
    
    # Access the database and collection
    db = client['data-analysis']
    collection = db['messages']
    
    # Query the collection for the user
    try:
        user_data = collection.find_one({'user': user})

        return user_data['threadid']
    except:
        return None

def get_file_id(user, filename):
    uri = "mongodb+srv://mishal0404:mishal2003@mishal0404.35lsnon.mongodb.net/?retryWrites=true&w=majority&appName=mishal0404"
    
    # Connect to MongoDB
    client = MongoClient(uri, server_api=ServerApi('1'))
    
    # Access the database and collection
    db = client['data-analysis']
    collection = db['files']
    
    # Query the collection for the user
    user_data = collection.find_one({'user': user}, {'files': 1, '_id': 0})
    
    if user_data and 'files' in user_data:
        # Loop through the files to find the filename
        for file in user_data['files']:
            if filename in file:
                return file[filename]
    
    # If the user or filename is not found, return None
    return None


def get_all_filenames(user):
    # MongoDB connection URI
    uri = "mongodb+srv://mishal0404:mishal2003@mishal0404.35lsnon.mongodb.net/?retryWrites=true&w=majority&appName=mishal0404"
    
    # Connect to MongoDB
    client = MongoClient(uri, server_api=ServerApi('1'))
    
    # Access the database and collection
    db = client['data-analysis']
    collection = db['files']
    
    # Query the collection for the user
    user_data = collection.find_one({'user': user}, {'files': 1, '_id': 0})
    
    if user_data and 'files' in user_data:
        # Extract filenames from the files list
        return user_data['files']
    
    # If the user or files are not found, return an empty list
    return []
    
def add_user_file(user, filename, file_id):
    # MongoDB connection URI
    uri = "mongodb+srv://mishal0404:mishal2003@mishal0404.35lsnon.mongodb.net/?retryWrites=true&w=majority&appName=mishal0404"
    
    # Connect to MongoDB
    client = MongoClient(uri, server_api=ServerApi('1'))
    
    # Access the database and collection
    db = client['data-analysis']
    collection = db['files']
    
    # Query the collection for the user
    update_result = collection.update_one(
        {'user': user},
        {'$addToSet': {'files': {filename:file_id}}},  # Use $addToSet to avoid duplicates
        upsert=True  # Create a new document if the user doesn't exist
    )

    # Check if the update was successful (at least 1 document modified)
    if update_result.modified_count >= 1:
      return True
    else:
      return False
    
def get_user_history(user):
    # MongoDB connection URI
    uri = "mongodb+srv://mishal0404:mishal2003@mishal0404.35lsnon.mongodb.net/?retryWrites=true&w=majority&appName=mishal0404"
    
    # Connect to MongoDB
    client = MongoClient(uri, server_api=ServerApi('1'))
    
    # Access the database and collection
    db = client['data-analysis']
    collection = db['messages']
    
    # Query the collection for the user
    try:
        user_data = collection.find_one({'user': user})

        return  [{"threadid":user_data["threadid"],"convo":user_data["convo"]}] + user_data['old']
    except:
        return None

def get_user_assistant(user):
    # MongoDB connection URI
    uri = "mongodb+srv://mishal0404:mishal2003@mishal0404.35lsnon.mongodb.net/?retryWrites=true&w=majority&appName=mishal0404"
    
    # Connect to MongoDB
    client = MongoClient(uri, server_api=ServerApi('1'))
    
    # Access the database and collection
    db = client['data-analysis']
    collection = db['messages']
    
    # Query the collection for the user
    try:
        user_data = collection.find_one({'user': user})

        return user_data['assistantid']
    except:
        return None
    
def convo(user, umsg, amsg):
    # MongoDB connection URI
    messages = [{"role":"user", "content":umsg},{"role":"assistant", "content":amsg}]
    uri = "mongodb+srv://mishal0404:mishal2003@mishal0404.35lsnon.mongodb.net/?retryWrites=true&w=majority&appName=mishal0404"
    
    # Connect to MongoDB
    client = MongoClient(uri, server_api=ServerApi('1'))
    
    # Access the database and collection
    db = client['data-analysis']
    collection = db['messages']
    
    # Query the collection for the user
    try:
        result = collection.update_one({'user': user}, {"$push": {"convo": {"$each": messages}}})
        # Return True if insertion is successful, False otherwise
        return result.modified_count > 0
    except: 
        return None


def create_user_thread(user, threadid):
    # MongoDB connection URI
    uri = "mongodb+srv://mishal0404:mishal2003@mishal0404.35lsnon.mongodb.net/?retryWrites=true&w=majority&appName=mishal0404"
    
    # Connect to MongoDB
    client = MongoClient(uri, server_api=ServerApi('1'))
    
    # Access the database and collection
    db = client['data-analysis']
    collection = db['messages']
    
    # Check if the user exists
    existing_user = collection.find_one({'user': user})
    
    if  not existing_user:
        # If user doesn't exist, create a new user with the provided message
        result = collection.insert_one({'user': user, 'threadid': threadid})
        
        # Return True if insertion is successful, False otherwise
        return result.acknowledged
    else: 
        return None
    
def update_user_thread(user, threadid):
    # MongoDB connection URI
    uri = "mongodb+srv://mishal0404:mishal2003@mishal0404.35lsnon.mongodb.net/?retryWrites=true&w=majority&appName=mishal0404"
    
    # Connect to MongoDB
    client = MongoClient(uri, server_api=ServerApi('1'))
    
    # Access the database and collection
    db = client['data-analysis']
    collection = db['messages']
    
    # Check if the user exists
    existing_user = collection.find_one({'user': user})
    oldthread = existing_user["threadid"]
    oldconvo = existing_user["convo"]
    mys = {"threadid":oldthread, "convo":oldconvo}
    if existing_user:
        # If user doesn't exist, create a new user with the provided message
        result = collection.update_one({'user': user}, {'$set': {'threadid': threadid, 'convo':[]}, "$push": {"old": {
                        '$each': [mys],
                        '$slice': -10
                    } }})
        # Return True if insertion is successful, False otherwise
        return result.modified_count > 0
    else: 
        return None
    
  
def update_user_assistant(user, assistantid):
    # MongoDB connection URI
    uri = "mongodb+srv://mishal0404:mishal2003@mishal0404.35lsnon.mongodb.net/?retryWrites=true&w=majority&appName=mishal0404"
    
    # Connect to MongoDB
    client = MongoClient(uri, server_api=ServerApi('1'))
    
    # Access the database and collection
    db = client['data-analysis']
    collection = db['messages']
    
    existing_user = collection.find_one({'user': user})

    if existing_user:
        # If user doesn't exist, create a new user with the provided message
        result = collection.update_one({'user': user}, {'$set': {'assistantid': assistantid }})
        # Return True if insertion is successful, False otherwise
        return result.modified_count > 0
    else: 
        return None
    

