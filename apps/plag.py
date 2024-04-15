import functools
from apps import utils
from flask import (
    Blueprint, flash, g, redirect, jsonify, request, make_response, url_for
)


plagbp = Blueprint('plag', __name__, url_prefix='/plag')


'''
POST req JSON format:
{
    simThreshold: int, (optional)
    answers: [
        {
            studentId: Id,
            answer: String
        },
        .
        .
        .
    ],
}

res JSON format:
[
    {
        "simScore": 0.7023688160354278,
        "student1": 2,
        "student2": 3
    },
    {
        "simScore": 0.9201858322653276,
        "student1": 1,
        "student2": 2
    }
]
'''
@plagbp.route('/', methods=(['POST']))
def plag_cosine():
    if request.is_json:
        json_data = request.json
        simThreshold = json_data.get('simThreshold', 0.7)

        answers = json_data['answers']
    else:
        error = {'message': 'Invalid JSON data'}
        return jsonify(error), 400

    # print(answers)
    ans_dic = {}
    for i in answers:
        ans_dic[i['studentId']] = i['answer']

    plagResults = utils.checkStringPlag(ans_dic)

    res = [i for i in plagResults if i['simScore'] >= simThreshold]    

    return jsonify(res), 200


'''
POST req JSON format:
{
    answer: string
}
'''
@plagbp.route('/copyleaks', methods=(['POST']))
def plag_copyleaks():
    if request.is_json:
        json_data = request.json
        answer = json_data['answer']
    else:
        error = {'message': 'Invalid JSON data'}
        return jsonify(error), 400
    
    utils.copyleaksApi(answer)

    response = make_response("OK", 200)
    return response

@plagbp.route('/copyleaks/completed', methods=(['POST']))
def copyleaksTest():

    if (request.method == "POST"):
        json_data = request.json
        res = json_data

    print(res)
    response = make_response("OK", 200)
    return response


@plagbp.route('/copyleaks/webhook/completed', methods=(['POST']))
def copyleaksComp():

    if (request.method == "POST"):
        json_data = request.json
        res = json_data['results']['score']

    print(res['aggregatedScore'])
    response = make_response("OK", 200)
    return response

@plagbp.route('/copyleaks/webhook/creditschecked', methods=(['POST']))
def copyleaksCheck():
    if (request.method == "POST"):
        json_data = request.json
        res = json_data['credits']

    print(res)

    response = make_response("OK", 200)
    return response
