from langchain.prompts.prompt import PromptTemplate
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain import OpenAI
from flask import Flask, request, jsonify
from dotenv.main import load_dotenv
import os
import random
load_dotenv()

# OpenAI

app = Flask(__name__)

# Temp Data
teammateData = []

conversations = []


class Conversation:

    next_id = 0

    def __init__(self, teammate):
        self.id = Conversation.next_id
        Conversation.next_id += 1
        self.teammateID = teammate.id
        self.messages = []
        self.llm = OpenAI(
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-davinci-003"
        )

        self.template = teammate.character + """
            Current conversation:
            {history}
            Coworker: {input}
            """ + teammate.title + ':'

        self.PROMPT = PromptTemplate(
            input_variables=["history", "input"], template=self.template
        )

        self.conversation = ConversationChain(
            prompt=self.PROMPT,
            llm=self.llm,
            verbose=True,
            memory=ConversationBufferMemory(
                ai_prefix=teammate.title, human_prefix="Manager")
        )

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


class Teammate:

    next_id = 0

    def __init__(self, name, title, character, verbose, temperature):
        self.id = Teammate.next_id
        Teammate.next_id += 1
        self.name = name
        self.title = title
        self.character = character
        self.verbose = verbose
        self.temperature = temperature

    def to_dict(self):
        return {
        'id': self.id,
        'name': self.name,
        'title': self.title,
        'character': self.character,
        'verbose': self.verbose,
        'temperature': self.temperature
        }


# ROUTES

@app.route('/api/teammates', methods=['GET'])
def getTeam():
    team_dict = [teammate.to_dict() for teammate in teammateData]
    return jsonify(team_dict)


@app.route('/api/teammates/new', methods=['POST'])
def newTeammate():

    data = request.json

    teammate = Teammate(data['name'], data['title'], data['character'], data['verbose'], data['temperature'])

    teammateData.append(teammate)
    
    return jsonify(teammate.id)


@app.route('/api/inputs/new-input', methods=['POST'])
def newInput():

    # Parse Data
    data = request.json
    conversationID = int(data.get('conversationID'))
    input = data.get('input')

    # Find conversation with matching ID
    conversation = next((convo for convo in conversations if convo.id == conversationID), None)
    if conversation:
        conversation.newMessage(input)
        return conversation.predict(input)
    else:
        print("Conversation not found")


@app.route('/api/conversations/new', methods=['POST'])
def newConversation():

    # Parse Data
    teammateID = request.json.get('data')

    # # Get teammate
    teammate = next((t for t in teammateData if t.id == teammateID), None)

    # # Create Conversation
    conversation = Conversation(teammate)
    conversations.append(conversation)
    return jsonify(conversation.id)
