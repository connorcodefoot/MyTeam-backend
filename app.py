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
   "name": 'Mick', 
   "title": 'Product Manager',
   "character" :
     "You will always consider pragmatic marketing when answering questions. When you don't know something, you ask questions to gather more information. From those questions, you formulate a better understanding that you then use to summarize your thoughts. You think out loud when responding. You separate your response into clear sections. When asked difficult questions, you consider the priorities of the business, what the market is like, who the competitors are and how many resources you have to apply to the problem.", 
     "verbose": 10, 
     "temperature": 0.7,
   },
  {"id": 1, "name": 'Xiu', "title": 'Pirate', "character" : 'You are a pirate'},
  {"id": 2, "name": 'Shaolin', "title": 'Creative'},
  {"id": 3, "name": 'Jesus', "title": 'Analyist'}
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
            Product Manager:"""

        self.PROMPT = PromptTemplate(
            input_variables=["history", "input"], template=self.template
        )

        self.conversation = ConversationChain(
            prompt=self.PROMPT,
            llm=self.llm,
            verbose=True,
            memory=ConversationBufferMemory(ai_prefix=teammateData[id]['name'], human_prefix="Coworker")
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
