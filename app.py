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
    "conversation_id": 0,
   },
  {"id": 1, "name": 'Xiu', "title": 'Developer'},
  {"id": 2, "name": 'Shaolin', "title": 'Creative'},
  {"id": 3, "name": 'Jesus', "title": 'Analyist'}
  ]

conversations = [
    {"id": 0, "teammateID": 0 },
    {"id": 1, "teammateID": 1 },
    {"id": 2, "teammateID": 2 },
    {"id": 3, "teammateID": 3 }
]

messages = [
    {"id": 0, "teammateID": 0, "conversationID": 0, "to": 0, "from": 0, "content": "Conversation 0" },
    {"id": 1, "teammateID": 1, "conversationID": 0, "to": 0, "from": 0, "content": "Conversation 1" },
    {"id": 2, "teammateID": 2, "conversationID": 0, "to": 0, "from": 0, "content": "Conversation 2" },
    {"id": 3, "teammateID": 3, "conversationID": 0, "to": 0, "from": 0, "content": "Conversation 3" },
]

class Conversation:

    llm = OpenAI(
	    temperature=0,
	    openai_api_key= os.getenv("OPENAI_API_KEY"),
	    model_name="text-davinci-003"
    )
    template = teammateData[0]['character'] + """
        Current conversation:
        {history}
        Coworker: {input}
        Product Manager:"""
    
    PROMPT = PromptTemplate(
        input_variables=["history", "input"], template=template
    )   

    conversation = ConversationChain(
    prompt=PROMPT,
	llm=llm,
    verbose=True,
	memory=ConversationBufferMemory(ai_prefix="Product Manager", human_prefix="Coworker")
    )

    def __init__(self, id):

        self.id = id


oneConvo = Conversation(0)



# first initialize the large language model


# now initialize the conversation chain


@app.route('/api/teammates', methods=['GET'])
def getTeam():
    return teammateData

@app.route('/api/inputs/new-input', methods=['POST'])
def newInput():
    return oneConvo.conversation.predict(input=str(request.data))

@app.route('/api/conversations/new' , methods =['POST'])
def newConversation():
    data = request.get_json()
    conversation_id = data.get('data')
    conversation = Conversation(conversation_id)
    print(conversation)
    return jsonify({'conversation_id': conversation.id})
