import json
import sys
import os
import  shutil
from flask import Flask
from flask import request
import jwt
from jwt.algorithms import RSAAlgorithm
import urllib.request
import json
import {app_module_name}

def validate_jwt_token(jwt_token):
    if jwt_token == None:
        raise Exception("Invalid authentication header")

    token_array = jwt_token.split(" ")
    if len(token_array) != 2:
        raise Exception("Invalid authentication header")

    token = token_array[1]

    try:
        decoded_unverified = jwt.decode(token, verify=False)
    except:
        raise Exception("Error decoding token")

    iss = decoded_unverified["iss"]
    aud = decoded_unverified["aud"]

    if aud == None:
        raise Exception("Invalid token aud")

    if iss == None:
        raise Exception("Invalid token iss")

    targetUrl = iss + ".well-known/jwks.json"

    try:
        jsonurl = urllib.request.urlopen(targetUrl)
        jwks = json.loads(jsonurl.read())
    except:
        raise Exception("Error requesting keys from token issuer")

    try:
        unverified_header = jwt.get_unverified_header(token)
        if unverified_header["alg"] == "HS256":
            raise Exception("Invalid keys alg")

        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
        public_key = RSAAlgorithm.from_jwk(json.dumps(rsa_key))

        decoded = jwt.decode(token, public_key, algorithms='RS256', audience=aud)
        if aud == decoded["aud"]:
            return decoded
    except:
        raise Exception("Error validating token")

    raise Exception("Unhandled error processing token")

_flask_app_ = Flask(__name__)

@_flask_app_.route('/', methods=['POST', 'OPTIONS', 'GET'])
def flask_app_serve_root():
    auth_enabled = {auth_enabled}
    if auth_enabled:
        authToken = request.headers.get('authorization')
        try:
            claim = validate_jwt_token(authToken)
        except:
            return "Unauthorized. Auth token invalid", 401

        if claim == None:
            return "Unauthorized", 401
            
    if request.method == 'OPTIONS':
        return json.dumps({}).encode('utf-8')

    if request.method == 'POST':
        content = ""
        response = {}
        try:
            if request.is_json:
                content = request.get_json()
            else:
                content = json.loads(request.data)

            response = {app_module_name}.{app_request_handler_function}(content)

        except:
            return "Malformed request", 400

        return json.dumps(response).encode('utf-8')

    
    return "Not implemented", 501

print("Initializing: {app_module_name}.{init_function}")
{app_module_name}.{init_function}()
print("Initialization complete")

if __name__ == '__main__':
    _flask_app_.run(debug=False, host='0.0.0.0')
