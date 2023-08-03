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
import pvleopard
picovoice_access_key = os.getenv("PICOVOICE_ACCESS_KEY")
handle = pvleopard.create(picovoice_access_key)

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
        self.llm = OpenAI(
            temperature=teammate["creativity"],
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-davinci-003"
        )

        # self.template = teammate["persona"] + """
        #     Current conversation:
        #     {history}
        #     Coworker: {input}
        #     """ + teammate["title"] + ':'

        # self.PROMPT = PromptTemplate(
        #     input_variables=["history", "input"], template=self.template
        # )

        # self.conversation = ConversationChain(
        #     prompt=self.PROMPT,
        #     llm=self.llm,
        #     verbose=True,
        #     memory=ConversationBufferMemory(
        #         ai_prefix=teammate["title"], human_prefix="Human")
        # )

        # self.googleTool = Tool(
        #     name="Google Search",
        #     description="Search Google for recent results.",
        #     func=search.run,
        # )

    def print_conversation(self):
        print("Conversation ID:", self.id)
        print("Conversation Chain:", self.conversation)

    def predict(self, input):
        return self.conversation.predict(input=str(input))

    def newMessage(self, message):
        self.messages.append({
            'id': len(self.messages) + 1,
            'message': message
        })

# Custom JSON Encoder class
class PersonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Conversation):
            # Convert Conversation object to a dictionary representation
            return {'name': obj.name, 'age': obj.age}
        # For other types, use the default encoder behavior
        return json.JSONEncoder.default(self, obj)
# ROUTES

@app.route('/api/teammates', methods=['GET'])
def getTeam():
    team_dict = [teammate.to_dict() for teammate in teammateData]
    return jsonify(team_dict)


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

    # Find conversation with matching ID
    conversation = next((convo for convo in conversations if convo.id == conversation_id), None)
    if conversation and "search" in input:
        conversation.newMessage(input)
        return conversation.googleTool.run(input)
    if conversation:
        conversation.newMessage(input)
        return conversation.predict(input)
    else:
        print("Conversation not found")

@app.route('/api/messages/new-message-audio', methods=['POST'])
def newMessageAudio():
 
    print('request received')

    # Retrieve Data
    conversation_id = request.form['conversationID']
    audio = request.files['file']

    # Save audio and get transcript
    audio_filename = secure_filename(audio.filename)
    audio_path = os.path.join('audioMessages', audio_filename)
    audio.save(audio_path)
    transcript, words = handle.process_file(audio_path)

    # Find conversation with matching ID
    conversation = next((convo for convo in conversations if convo.id == conversation_id), None)
    if conversation:
        conversation.newMessage(transcript)
        return conversation.predict(transcript)
    else:
        print("Conversation not found")


@app.route('/api/conversations/new', methods=['POST'])
def newConversation():

    # Parse Data
    teammateID = request.json.get('data')

    # Get teammate from DB
    teammate = supabase.table("teammates").select("*").eq("id", teammateID).execute()

    teammate = teammate.data[0]

    # Create conversation object
    conversation = Conversation(teammate)
    conversationJSON = json.dumps(conversation.__dict__)
    conversationJSON = json.loads(conversationJSON)


    # Add conversation to DB
    conversationDB = supabase.table("conversations").insert(conversationJSON).execute()
    print(conversationDB)

    # print(conversationDB)

    # # Create Conversation
    
    # return jsonify(conversation.id)
