# General Config
from flask import Flask, request, jsonify, json
from dotenv.main import load_dotenv
from werkzeug.utils import secure_filename
import os
import math

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

# Picovoice 
# import pvleopard
# picovoice_access_key = os.getenv("PICOVOICE_ACCESS_KEY")
# handle = pvleopard.create(picovoice_access_key)

# Initiate App
app = Flask(__name__)

# Temp Data

database = supabase.table("teammates").select("*").execute() 

teammateData = []

conversations = []

class Conversation:

    def __init__(self, teammate):
        self.teammateID = teammate["id"]
        # self.messages = []
        self.llm_type = 'OpenAI'
        self.teammate_temperature = teammate["creativity"]
        self.model_name = "text-davinci-003"
        self.teammate_persona = teammate["persona"]
        self.teammate_title = teammate["title"]


    def initializeConversation(self):

        llm= OpenAI(
            temperature=self.teammate_temperature,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model_name= self.model_name
        )

        conversation_template = self.teammate_persona + """
            Current conversation:
            {history}
            Coworker: {input}
            """ + self.teammate_title + ':'

        createPrompt = PromptTemplate(
            input_variables=["history", "input"], template= conversation_template
        )

        ConversationChain(
            prompt=createPrompt,
            llm=llm,
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
            'teammateID': self.teammateID,
            # 'messages': self.messages,
            'llm_type': self.llm_type,
            'teammate_temperature': self.teammate_temperature,
            'model_name': self.model_name,
            'teammate_persona': self.teammate_persona,
            'teammate_title': self.teammate_title
        }

    def print_conversation(self):
        print("Conversation ID:", self.id)
        print("Conversation Chain:", self.conversation)

    def predict(self, input):
        return self.conversation_thread.predict(input=str(input))

    def newMessage(self, message):
        self.messages.append({
            'id': len(self.messages) + 1,
            'message': message
        })

# ROUTES

@app.route('/api/teammates', methods=['GET'])
def getTeam():

    teammates = supabase.table("teammates").select('*').execute()
    print(teammates)

    return jsonify(teammates.data)


@app.route('/api/teammates/new', methods=['POST'])
def newTeammate():

    data = request.json

    # Create new DB record
    newTeammate = supabase.table("teammates").insert(data).execute()

    # Create new conversation
    return jsonify(newTeammate.data[0]['id'])


@app.route('/api/messages/new-message-text', methods=['POST'])
def newMessage():

    # Parse Data
    data = request.json
    conversation_id = int(data.get('conversationID'))
    input = data.get('input')


    conversation = supabase.table("conversations").select('id').eq('id', conversation_id)

    return conversation.conversation_thread.predict(input=str(input))

    # # Find conversation with matching ID
    # conversation = next((convo for convo in conversations if convo.id == conversation_id), None)
    # if conversation and "search" in input:
    #     conversation.newMessage(input)
    #     return conversation.googleTool.run(input)
    # if conversation:
    #     conversation.newMessage(input)
    #     return conversation.predict(input)
    # else:
    #     print("Conversation not found")

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
    teammateID = request.json.get('data')

    # Get teammate from DB
    teammate = supabase.table("teammates").select("*").eq("id", teammateID).execute()

    teammate = teammate.data[0]

    # Create conversation object
    conversation = Conversation(teammate)
    conversationJSON = conversation.to_json()
    print(conversationJSON)


    # Add conversation to DB
    conversationDB = supabase.table("conversations").insert(conversationJSON
    ).execute()
    print("conversationDB:", conversationDB)

    # # Create Conversation

    conversation.conversation_thread = conversation.initializeConversation()
    
    return jsonify(conversationDB.data[0]['id'])
