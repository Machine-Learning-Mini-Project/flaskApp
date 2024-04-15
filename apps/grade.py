import functools
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.output_parsers.openai_tools import JsonOutputToolsParser
from langchain_core.tools import tool

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


    