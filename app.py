from flask import Flask, request
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
     "temperature": 0.7
   },
  {"id": 1, "name": 'Xiu', "title": 'Developer'},
  {"id": 2, "name": 'Shaolin', "title": 'Creative'},
  {"id": 3, "name": 'Jesus', "title": 'Analyist'}
  ]

# first initialize the large language model
llm = OpenAI(
	temperature=0,
	openai_api_key= os.getenv("OPENAI_API_KEY"),
	model_name="text-davinci-003"
)

template = teammateData[0]['character'] + """
Current conversation:
{history}
Human: {input}
Product Manager:"""
PROMPT = PromptTemplate(
    input_variables=["history", "input"], template=template
)

# now initialize the conversation chain
conversation = ConversationChain(
    prompt=PROMPT,
	llm=llm,
    verbose=True,
	memory=ConversationBufferMemory(human_prefix="Product Manager")
)

@app.route('/api/teammates', methods=['GET'])
def getTeam():
    return teammateData

@app.route('/api/inputs/new-input', methods=['POST'])
def newInput():
    return conversation.predict(input=str(request.data))

