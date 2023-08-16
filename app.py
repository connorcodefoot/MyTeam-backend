# General Config
from flask import Flask, request, jsonify
from dotenv.main import load_dotenv
import os

load_dotenv ()

# Supabase
from supabase import create_client
supabaseURL = os.environ.get("SUPABASE_URL")
supabaseKey = os.environ.get("SUPABASE_KEY")
supabase = create_client(supabaseURL, supabaseKey)

# LangChain and OpenAI
from langchain.prompts.prompt import PromptTemplate
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain import OpenAI
from langchain.tools import Tool
from langchain.utilities import GoogleSearchAPIWrapper

## Google Search for Langchain global params
google_api_key= os.getenv("GOOGLE_API_KEY")
google_cse_id= os.getenv("GOOGLE_CSE_ID")
search = GoogleSearchAPIWrapper()

# Initiate App
app = Flask(__name__)

# APPLICATION

# Classes

class Conversation:

    def __init__(self, data):
        self.id = data['id']
        self.teammateID = data['teammateID']
        self.messages = []
        self.llm_type = data['llm_type']
        self.teammate_temperature = data['teammate_temperature']
        self.model_name = "text-davinci-003"
        self.teammate_name = data['teammate_name']
        self.teammate_persona = data['teammate_persona']
        self.teammate_title = data['teammate_title']

        self.llm= OpenAI(
            temperature=self.teammate_temperature,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model_name= self.model_name
        )

        self.conversation_template = self.teammate_persona + """
            Current conversation:
            {history}
            Coworker: {input}
            """ + self.teammate_name + ':'

        self.createPrompt = PromptTemplate(
            input_variables=["history", "input"], template= self.conversation_template
        )

        self.conversation_thread = ConversationChain(
            prompt=self.createPrompt,
            llm=self.llm,
            verbose=True,
            memory=ConversationBufferMemory(
                ai_prefix=self.teammate_title, human_prefix="Human")
        )

        self.googleTool = Tool(
            name="Google Search",
            description="Search Google for recent results.",
            func=search.run,
        )
    
    def to_json(self):
        return {
            'id': self.id,
            'teammateID': self.teammateID,
            'messages': self.messages,
            'llm_type': self.llm_type,
            'teammate_temperature': self.teammate_temperature,
            'model_name': self.model_name,
            'teammate_name': self.teammate_name,
            'teammate_persona': self.teammate_persona,
            'teammate_title': self.teammate_title
        }

    def print_conversation(self):
        print("Conversation ID:", self.id)
        print("Conversation Chain:", self.conversation)

    def predict(self, message):
        return self.conversation_thread.predict(input=str(message))

    def new_message(self, message):
        self.messages.append({
            "id": message['id'],
            "message": message['message'],
            "from": message['from'],
            "to": message["to"]
        })

# IMPORT TEAMMATE DATA

teammate_data = supabase.table("teammates").select('*').execute()
teammate_data = teammate_data.data

# IMPORT CONVERSATION DATA AND CREATE INSTANCES
conversation_data = []
conversation_data_raw = supabase.table("conversations").select('*').execute()

for conversation in conversation_data_raw.data:

    conversation_data.append(Conversation(conversation))

# IMPORT MESSAGE DATA AND ADD TO CONVERSATIONS

message_data = supabase.table("messages").select('*').execute()
message_data = message_data.data

for message in message_data:

    conversation_id = message['conversation_id']

    for conversation in conversation_data:

        conversation_json = conversation.to_json()
        
        if conversation_json['id'] == conversation_id:
            
            conversation.new_message(message)

# ROUTES

@app.route('/api/load', methods=['GET'])
def loadApp():

    conversation_data_json = [conversation.to_json() for conversation in conversation_data]

    print(conversation_data_json)

    
    return jsonify(teammate_data, conversation_data_json)
    


@app.route('/api/teammates', methods=['GET'])
def getTeam():

    teammates = supabase.table("teammates").select('*').execute()

    return jsonify(teammates.data)


@app.route('/api/teammates/new', methods=['POST'])
def newTeammate():

    data = request.json

    # Create new DB record
    newTeammate = supabase.table("teammates").insert(data).execute()

    teammate_data.append(newTeammate.data[0])

    # Create new conversation
    return jsonify(newTeammate.data[0]['id'])


@app.route('/api/messages/new-message-text', methods=['POST'])
def newMessage():

    # Parse Data
    message = request.json

    conversation_id = message['conversationID']
    message = message['input']

    for convo in conversation_data:

        convo_data_json = convo.to_json()

        if convo_data_json['id'] == conversation_id:

            message_response = convo.predict(message)
            message_response = str(message_response)
           
            message_from_user = supabase.table("messages").insert({
                "conversation_id": conversation_id,
                "teammateID": convo_data_json['teammateID'],
                "to": convo_data_json['teammate_name'],
                "from": 'You',
                "message": message 
            }).execute()

            message_to_user = supabase.table("messages").insert({
                "conversation_id": conversation_id,
                "teammateID": convo_data_json['teammateID'],
                "to": 'user',
                "from": convo_data_json['teammate_name'],
                "message": message_response 
            }).execute()

            convo.new_message(message_from_user.data[0])
            convo.new_message(message_to_user.data[0])

            return message_response


        


# @app.route('/api/messages/new-message-audio', methods=['POST'])
# def newMessageAudio():
 
#     print('request received')

#     # Retrieve Data
#     conversation_id = request.form['conversationID']
#     audio = request.files['file']

#     # Save audio and get transcript
#     audio_filename = secure_filename(audio.filename)
#     audio_path = os.path.join('audioMessages', audio_filename)
#     audio.save(audio_path)
#     transcript, words = handle.process_file(audio_path)

#     # Find conversation with matching ID
#     conversation = next((convo for convo in conversations if convo.id == conversation_id), None)
#     if conversation:
#         conversation.newMessage(transcript)
#         return conversation.predict(transcript)
#     else:
#         print("Conversation not found")


@app.route('/api/conversations/new', methods=['POST'])
def newConversation():

    # Parse Data
    teammateID = request.json['teammateID']   

    # Get teammate from DB
    teammate = supabase.table("teammates").select("*").eq("id", teammateID).execute()
    teammate = teammate.data[0]

    conversation_insert = supabase.table("conversations").insert({
        "teammateID": teammate['id'], 
        "teammate_name" : teammate['name'], 
        "teammate_temperature": teammate['creativity'], 
        "teammate_persona" : teammate['persona'], 
        "teammate_title" : teammate['title']
    }).execute()

    # Create conversation object and itialize conversation with LLM
    conversation = Conversation(conversation_insert.data[0])
    conversation_data.append(conversation)
    print(conversation_data)

    conversation = conversation.to_json()
    
    return conversation
