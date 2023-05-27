from flask import Flask, request
from dotenv.main import load_dotenv
import os
load_dotenv()

# OpenAI
from langchain import OpenAI
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts.prompt import PromptTemplate


# first initialize the large language model
llm = OpenAI(
	temperature=0,
	openai_api_key= os.getenv("OPENAI_API_KEY"),
	model_name="text-davinci-003"
)

template = """This is a conversation between a human and Pirate that talks a lot about the sea whenever they can 

Current conversation:
{history}
Human: {input}
Pirate:"""
PROMPT = PromptTemplate(
    input_variables=["history", "input"], template=template
)

# now initialize the conversation chain
conversation = ConversationChain(
    prompt=PROMPT,
	llm=llm,
    verbose=True,
	memory=ConversationBufferMemory(human_prefix="Pirate")

    
)

app = Flask(__name__)

@app.route('/api/new-input', methods=['POST'])
def newInput():
    return conversation.predict(input=str(request.data))

