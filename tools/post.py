import urllib.request
import json

url = "http://localhost:5006"
hdr = { 
    'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)',
    'authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6Ik1qWkdPRVE0TWpJNE1Ea3hOVGc0TVVZek1EZ3lOa1l4UXpBeFFUWkRRakl4T0RNMVEwWTFNZyJ9.eyJpc3MiOiJodHRwczovL2Rldi0yYzNvNHl0ci5hdXRoMC5jb20vIiwic3ViIjoibGxOZkFSRXdRekR4VVJpeDZlTWVVS25oaVBFZmVJUXVAY2xpZW50cyIsImF1ZCI6Im15YXBpIiwiaWF0IjoxNTU3OTQzOTkzLCJleHAiOjE1NTgwMzAzOTMsImF6cCI6ImxsTmZBUkV3UXpEeFVSaXg2ZU1lVUtuaGlQRWZlSVF1IiwiZ3R5IjoiY2xpZW50LWNyZWRlbnRpYWxzIn0.shjJfetS_-NvDnAXtAKwFvS9GlRqAtIMXUTX4tCKgTym-boL01CbyDPV2zKbQoTYmZ3D_fpr8Ac3sDAyL1xNlrCnu54flkX-L1fB8JSXTZyRKdWZi-frJJtaDzOVm99gJjy1bpgoD4Unl8ICIocQ9C2cWLN_NanJZYGl8o85He5amZV7WHFp1QHsN8g4hrJ0VO2_nImUwZ-T6mP0H36l-cNO9e4xAqUKRqE1Ohrl63bZ_M1XtB_H9JshaMHi-Fbgvm6w2yKULD-4W3OmIe0qglf5gKIF5HKRVAMQYq6NabsbpeiUJ3RTKSxqjYT8XqSU_qXXvH2FYmsJzrE99YHRcQ',
    'Content-Type': 'application/json'
}

data = json.dumps({'spam': 1, 'eggs': 2, 'bacon': 0})

jsondataasbytes = data.encode('utf-8') 

req = urllib.request.Request(url, jsondataasbytes, headers=hdr)
response = urllib.request.urlopen(req)
content = response.read()

response_json = json.loads(content)
print(response_json)
