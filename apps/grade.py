import functools
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.output_parsers.openai_tools import JsonOutputToolsParser
from langchain_core.tools import tool
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent

from openai import OpenAI
openAiClient = OpenAI()
import json 

from flask import (
    Blueprint, flash, g, redirect, jsonify, request, session, url_for
)


gradebp = Blueprint('grade', __name__, url_prefix='/grade')



class qOutputType(BaseModel):
    points: int = Field(description="points given to the answer")
    feedback: str = Field(description="feedback for the answer")

'''
subjectiveQ - for answering subjective questions
POST req JSON format:
{
    question: string
    points: int
    instruction: string
    answer: string
}

res JSON format:
{
    points: int
    feedback: string
}
'''
@gradebp.route('/', methods=(['POST']))
def subjectiveQ():

    if request.is_json:
        json_data = request.json
        question = json_data['question']
        points = json_data['points']
        instruction = json_data['instruction']
        answer = json_data['answer']
    else:
        error = {'message': 'Invalid JSON data'}
        return jsonify(error), 400

    
    model = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0).bind_tools([qOutputType])
    
    opParser = JsonOutputToolsParser()

    prompt= ChatPromptTemplate.from_messages(
        [
            ("system", 
            "You have to give points to a user-generated answer to a question and provide feedback for the same.\n\
            This is the question the user tried to answer: {question}\n\
            Total possible points are: {points}\n\
            This is your instruction on how to give points: {instruction}\n\
            Return the number of points and provide feedback on answer in no more than 50 words.\
            If there is no answer, return 0 points."
            ),

            ("user", "{answer}")
        ],
    )

    chain = prompt | model | opParser

    res = chain.invoke({"question": question,
                  "points": points,
                  "instruction": instruction,
                  "answer": answer})    
    
    return jsonify(res[0]['args']), 200





'''
subjectiveQ - for answering subjective questions
POST req form format (refer postman):
    file: <actual file>
    question: string
    points: int
    instruction: string


res JSON format:
{
    points: int
    feedback: string
}
'''
@gradebp.route('/code', methods=(['POST']))
def codeQ():

    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    reqfile = request.files['file']
    if reqfile.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    question = request.form['question']
    points = request.form['points']
    instruction = request.form['instruction']


    file = openAiClient.files.create(
                file=reqfile.read(),
                purpose='assistants'
            )
    
    assistant = openAiClient.beta.assistants.create(
                    instructions= f"You have to give points to user-generated code and provide feedback for the same.\
                                    Interpret the code and assign points and feedback based on following\
                                    criteria:\n\
                                    This is the objective of the code: {question}\n\
                                    Total possible points are: {points}\n\
                                    This is your instruction on how to give points: {instruction}\n\
                                    Return the number of points and provide feedback on answer in no more than 50 words.\
                                    If there is no answer, return 0 points. Do not deduct points for lack of dependency ,instead try to give points\
                                    based on logic of code.\n\n\
                                    IMPORTANT: only return a json object with attributes points and feedback. DO NOT output any additional text outside of the JSON",
                    model="gpt-4-turbo",
                    tools=[{"type": "code_interpreter"}, 
                            ],
                    tool_resources={
                        "code_interpreter": {
                            "file_ids" : [file.id]
                        }
                    }
                    
                )

    thread = openAiClient.beta.threads.create()

    run = openAiClient.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id,
        additional_instructions="IMPORTANT: only return a json object with attributes points and feedback. DO NOT output any additional text outside of the JSON",\
        temperature = 0.1,
        # response_format= {"type": "json_object"}
    )

    if run.status == 'completed': 
        messages = openAiClient.beta.threads.messages.list(
            thread_id=thread.id,
        )
    else:
        print(run.status)


    # model = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0).bind_tools([qOutputType])
    
    # opParser = JsonOutputToolsParser()

    # prompt= ChatPromptTemplate.from_messages(
    #     [
    #         ("system", 
    #         "You have to find JSON in given user string and return it. If you cant find json create your own json\
    #             in format  [points: int, feedback: string] "
    #         ),

    #         ("user", "{answer}")
    #     ],
    # )

    # chain = prompt | model | opParser


    # res = chain.invoke({"answer": str(messages.data[0].content[0].text.value)})  

    print(type(messages.data[0].content[0].text.value))
    print(messages.data[0].content[0].text.value)   
    start_index = messages.data[0].content[0].text.value.find('{')
    end_index = messages.data[0].content[0].text.value.rfind('}') + 1

    if '```json' in messages.data[0].content[0].text.value:
        start_index = messages.data[0].content[0].text.value.find('```json') + len('```json') + 1
        end_index = messages.data[0].content[0].text.value.find('```', start_index)
        
        

    json_str = messages.data[0].content[0].text.value[start_index:end_index]

    res = json.loads(json_str)


    return jsonify(res), 200

    
