import os
from dotenv import load_dotenv

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


from copyleaks.copyleaks import Copyleaks
from copyleaks.exceptions.command_error import CommandError
from copyleaks.models.submit.document import FileDocument, UrlDocument, OcrFileDocument
from copyleaks.models.submit.properties.scan_properties import ScanProperties
from copyleaks.models.export import *
import base64
import random



'''
dictionary fromat: 
{
    Student1Id (int): answer (string),
    Student2Id (int): answer (string)
    .
    .
    .
}

returns list of dictionary
[
    {'studentId': id1, 
     'studentId': id2, 
     'simScore': sim_score
    },
    {'student1': id1, 
     'student2': id2, 
     'simScore': sim_score
    },
]
'''
def checkStringPlag(answers: dict):
    
    if(len(answers) < 2):
        return True
    
    corpus = list(answers.values())
    '''
    vectorize answers then transform to normalized tf or tf-idf representation
    The goal of using tf-idf instead of the raw frequencies of occurrence
    of a token in a given document  is to scale down the impact of tokens that occur very frequently in a given corpus and 
    that are hence empirically less informative than features that occur in a small fraction of the training corpus.
    '''    
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(corpus).toarray()
    s_vectors = list(zip(list(answers.keys()), X))


    #compare vector of each student with every other student using cosine similarity
    plagiarism_results = []
    for student_a, text_vector_a in s_vectors:
        new_vectors = s_vectors.copy()
        current_index = new_vectors.index((student_a, text_vector_a))
        del new_vectors[current_index]
        for student_b, text_vector_b in new_vectors:
            sim_score = cosine_similarity([text_vector_a, text_vector_b])[0][1]
            student_pair = sorted((student_a, student_b))
            score = {'student1': student_pair[0], 
                     'student2': student_pair[1], 
                     'simScore': sim_score  
                    }
            plagiarism_results.append(score)
        
        tuple_of_dicts = [tuple(sorted(d.items())) for d in plagiarism_results]
        unique_tuples = set(tuple_of_dicts)
        unique_dicts = [dict(t) for t in unique_tuples]

    return unique_dicts   


def copyleaksApi(answer):
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path)
    COPYLEAKS_API_KEY = os.getenv('COPYLEAKS_API_KEY')
    EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
    WEB_HOOK = os.getenv('WEB_HOOK')

    try:
        auth_token = Copyleaks.login(EMAIL_ADDRESS, COPYLEAKS_API_KEY)
    except CommandError as ce:
        response = ce.get_response()
        print(f"An error occurred (HTTP status code {response.status_code}):")
        print(response.content)

    print("Logged successfully!\n")

    ansEncoded = answer.encode('utf-8')
    BASE64_FILE_CONTENT = base64.b64encode(ansEncoded).decode('utf8')  # or read your file and convert it into BASE64 presentation.
    FILENAME = "Copy of AI_Experiment03.pdf"
    scan_id = random.randint(100, 100000)  # generate a random scan id
    file_submission = FileDocument(BASE64_FILE_CONTENT, FILENAME)


    #CHANGE TO NGROK URL
    url = WEB_HOOK + '/{STATUS}'
    scan_properties = ScanProperties(url)

    #VERY IMPORTANT
    scan_properties.set_sandbox(True)  # Turn on sandbox mode. Turn off on production.

    # scan_properties.set_action(1)   # To check credits


    file_submission.set_properties(scan_properties)
    Copyleaks.submit_file(auth_token, scan_id, file_submission)  # sending the submission to scanning
    print("Send to scanning")
    print("You will notify, using your webhook, once the scan was completed.")

