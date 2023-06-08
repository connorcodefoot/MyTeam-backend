from flask import Flask, request, jsonify
from dotenv.main import load_dotenv
import os
load_dotenv()

# OpenAI
from langchain import OpenAI
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts.prompt import PromptTemplate

app = Flask(__name__)

# Temp Data
teammateData = [
  {"id": 0, 
   "name": 'Orc', 
   "title": 'Orc Lord',
   "character" :
     "You are an orc and you are looking for hobits. You need to destroy the hobbits and find the ring before the hobits reach Mount Doom", 
     "verbose": 10, 
     "temperature": 0.7,
   },
  {"id": 1, "name": 'Frodo', "title": 'Hobbit', "character" : 'You are scared of everything and need to ask sam for help all the time. The fate of mankind lies in your hands'},
  {"id": 2, "name": 'Sam', "title": 'Hobbit', "character" : 'You are obssessed with food and have a crush on Frodo. You and him used to be married as a gay couple until you decided to recently take a break. You always wonder where he is and where food is'},
  {"id": 3, "name": 'Golum', "title": 'Creature', "character" : 'You talk like Golum from lord of the rings. You are obssessed with a ring and you have tourettes'}
  ]

conversations = []

class Conversation:
    def __init__(self, id):
        self.id = id
        self.messages = []
        self.llm = OpenAI(
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-davinci-003"
        )
        self.template = teammateData[id]['character'] + """
            Current conversation:
            {history}
            Coworker: {input}
            """ + teammateData[id]['title'] + ':'

        self.PROMPT = PromptTemplate(
            input_variables=["history", "input"], template=self.template
        )

        self.conversation = ConversationChain(
            prompt=self.PROMPT,
            llm=self.llm,
            verbose=True,
            memory=ConversationBufferMemory(ai_prefix=teammateData[id]['title'], human_prefix="Manager")
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
        

@app.route('/api/teammates', methods=['GET'])
def getTeam():
    return teammateData

@app.route('/api/inputs/new-input', methods=['POST'])
def newInput():

    # Parse Data
    data = request.json
    conversationID = int(data.get('conversationID'))
    input = data.get('input')

    # Get conversation
    # Find conversation with matching ID
    conversation = next((convo for convo in conversations if convo.id == conversationID), None)
    if conversation:
        conversation.newMessage(input)
        conversation.print_conversation()
        return conversation.predict(input)
    else:
        print("Conversation not found")

@app.route('/api/conversations/new' , methods =['POST'])
def newConversation():
    data = request.get_json()
    conversation_id = data.get('data')
    conversation = Conversation(conversation_id)
    conversations.append(conversation)
    return jsonify(conversation.id)
