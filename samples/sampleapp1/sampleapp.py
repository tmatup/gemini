import json
import sys
import os
import  shutil

def init():
	return 'App intialized'
	
def predict(requestData):
	requestData['responseKey'] = 'responseValue'
	return requestData

