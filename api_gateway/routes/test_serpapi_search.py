import http.client
import json
import urllib.parse

conn = http.client.HTTPSConnection("flipkart-apis.p.rapidapi.com")

headers = {
    "x-rapidapi-key": "e48b6982f7mshddc29aaa9b85ff1p187bc9jsna50ad86a869f",
    "x-rapidapi-host": "flipkart-apis.p.rapidapi.com"
}

query = "iphone 15"
encoded_query = urllib.parse.quote(query)

endpoint = f"/backend/rapidapi/search?query={encoded_query}&page=1"

conn.request("GET", endpoint, headers=headers)

res = conn.getresponse()
data = json.loads(res.read().decode("utf-8"))

print(data)
