import os
import warnings, logging
import subprocess
import importlib
import requests
from flask import Flask, jsonify, request
from flask import current_app, abort, Response
from hdfs import InsecureClient


logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
application = Flask(__name__)


@application.route('/config', methods=['POST'])
def config():
    # Read params from Json
    if not request.json \
    or not 'model_name' in request.json \
    or not 'handler' in request.json  \
    or not 'model' in request.json  \
    or not 'params' in request.json:
        abort(400)

    handler_file = request.json['handler']
    model_file = request.json['model']
    params_file = request.json['params']
    model_name = request.json['model_name']
    hdfs_uri = request.json['hdfs_uri']
    logger.info('Read json configurations: OK!!')
    
    # Download files from HDFS
    client_hdfs = InsecureClient(hdfs_uri)
    client_hdfs.download(handler_file, "./handler.py", overwrite=True)
    client_hdfs.download(model_file, "./model.py", overwrite=True)
    client_hdfs.download(params_file, "./params.pt", overwrite=True)
    logger.info('Download files: OK!!')
    
    # Install library dependencies
    response = os.popen(
        """torch-model-archiver --model-name %s --version 1.0 --model-file ./model.py --serialized-file ./params.pt --handler ./handler.py && mv %s.mar /home/model-server/model-store/"""%(model_name, model_name)).read().strip()
    current_app.hdfs_uri = hdfs_uri
    current_app.configured = True
    logger.info('Uploaded model: %s'%model_name)
    return jsonify({'response': response}), 201


@application.route('/raw', methods=['POST'])
def raw():
    # Read inputs/classes or Return reason of abort
    if not request.json \
    or not 'command' in request.json:
        abort(400)
    response = os.popen(request.json['command']).read().strip()
    logger.info('Visited raw page with bash command: \n%s'%request.json['command'])
    return jsonify({'response': response}), 201


@application.route('/')
def index():
    logger.info('Visited index page')
    return jsonify({'response': "index page"}), 201


if __name__ == '__main__':
    application.run(host='0.0.0.0', port=8079)
    
