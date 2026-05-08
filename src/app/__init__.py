import os
import sys

from kafka import KafkaProducer
print("Python used:", sys.executable)
from flask import Flask, json
from flask import request,jsonify
from app.service.messageService import MessageService

app = Flask(__name__)
app.config.from_pyfile('config.py')

messageService = MessageService()
producer = KafkaProducer(bootstrap_servers= os.getenv('KAFKA_HOST') + ':' + os.getenv('KAFKA_PORT'), 
                               value_serializer=lambda v: json.dumps(v).encode('utf-8'))

@app.route('/v1/ds/message',methods=['POST'])
def handle_message():
    message = request.json.get('message')
    result = messageService.process_message(message)
    if isinstance(result, list):
        return jsonify([item.dict() for item in result])
    
    elif result is not None and hasattr(result, "dict"):
        serialized_result = jsonify(result.dict())
       
        producer.send('expense_service', value=result.dict())
        return serialized_result 
    
    else:
        return jsonify(result)

@app.route('/',methods=['GET'])
def handle_get():
    print("hello world")


if __name__ == "__main__":
    app.run(host="localhost",port=8000,debug=True,use_reloader=False)


