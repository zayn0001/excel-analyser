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

        return user_data['old'] + [{"threadid":user_data["threadid"],"convo":user_data["convo"]}]
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
    

