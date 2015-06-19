import requests
import json
import re

NUM_POSTS = 10
GRAPH_API = 'https://graph.facebook.com/v2.3/autocustomersupport/feed?'
ACCESS_TOKEN = "CAACEdEose0cBAD4BeVx6iHS8zSdZCuk2Vea7zkIYD8GqFohj7mxZC5iG2qsUvaiQDxfzKKZB64GrNXgFsSnVdd6Limeab9pLPIwuGas1YsGaFTbgi4KpykIxadZBt1tT9PJcRPP0W2K09xNaWkqE1ksiMDyZB5ZC4ZBCQtbnvNMPl4CERcZBZAZA2rHYNZCkSWN4pMZD"
POST_API = 'https://graph.facebook.com/v2.3/'
sentiment_url = "http://text-processing.com/api/sentiment/"
POST_URL = "https://apiv2.indico.io/sentiment?key=77df8784f52f3175d9f4035ed1c6c0f7"

payload_oid = {"message" : "Please enter your order id so we can take the request further",
    				"access_token" : ACCESS_TOKEN}
payload_oid1 = {"message" : "a new ticket has been raised for your Order id ",
    				"access_token" : ACCESS_TOKEN}
payload_oid2 = {"message" : "We already have a ticket with your order id, we will get back to you ",
    				"access_token" : ACCESS_TOKEN}
cs_url = 'http://crm-platform-services.nm.flipkart.com/v1/incidentManager/get/Incidents/orderId/'
GENERIC_TEXT = "Please enter your order id so we can take the request further"

def sentiment_score(to_analyze):
    payload = {'data': to_analyze}
    r = requests.post(POST_URL,data=payload)
    #print(r.text)
    if(r.status_code == requests.codes.ok):
        json_data = r.json()
        return json_data

def extract_orderid(tweet_text):
    OD = re.search(r'\sOD[0-9]{18}',tweet_text)
    if(OD == None):
        return None
    return OD.group(0)

def form_fb_json(post):
    fb_post = {}
    fb_post['text'] = post['message']
    fb_post['user'] = post['from']['name']
    OD = extract_orderid(post['message'])
    sentiment_json = sentiment_score(post['message'])
    data  = {'fbpost': fb_post, 'OID': OD, 'sentiment_json':sentiment_json}
    return data

def getticketdata(order_id):
   result = {}
   result['status'] = "Ticket not created"
   if order_id == None:
   		return
   r = requests.get(cs_url + order_id)
   if not r.text:
       return result
   full_incidents = json.loads(r.text)
   if len(full_incidents) == 0 :
       return result
   last_index = len(full_incidents)-1
   last_incident = full_incidents[last_index]
   result['subject'] =  last_incident['Subject']
   result['category'] = last_incident['Product']['name']
   for threads in last_incident['Threads']['ThreadList']:
       result[str(threads['EntryType']['name']).lower()] = str(threads['Text']).lower()
   result['status'] = "Ticket"
  # print(str(result))
   return result

def check_no_oid(post,to_store):
    checks = {'Order','OD','order','ORDER'}
    generic_texts = {payload_oid['message'],payload_oid1['message'],payload_oid2['message']}
    if any(x in generic_texts for x in to_store['fbpost']['text']):
        return
    print("Message to Parse:" + to_store['fbpost']['text'])
   # print(to_store)
    sem = to_store['sentiment_json']['results']
    if round(sem*100)<20:
        if to_store['OID'] == None and any(x in to_store['fbpost']['text'] for x in checks):
           # print("-----neg ------" + str(to_store))
            print("ACTION:Negative post with no order id, reminding customer to post order id")
            message = POST_API + "" + post['id'] + "/comments"
            r = requests.post(message,payload_oid)
           # print("fb post-------" + r.text)
        else:
            tktinfo = getticketdata(to_store['OID'])
         #   print("-----neg ------WITH OID" + str(to_store))
            message = POST_API + "" + post['id'] + "/comments"
            #r = requests.post(message,payload_oid)
           # print("fb post with oid-------" + r.text)
            if tktinfo['status'] == "Ticket not created":
                print("ACTION:Negative text and No ticket for Order id = " + to_store['OID'])
                r = requests.post(message,payload_oid1)
              #  print("fb post with oid-------" + r.text)
            else:
                print("ACTION:Negative text and Ticket already opened! subject=" + tktinfo['subject'])
                r = requests.post(message,payload_oid2)
               # print("fb post with oid-------" + r.text)

def getfbposts():
    url = GRAPH_API + "access_token=" + ACCESS_TOKEN + "&limit=" + str(NUM_POSTS)
    #print(url)
    r = requests.get(url)
    json_data = json.loads(r.text)
    posts = json_data['data']
    json_blob = {}
    counter = 0
    #print("---------POST-------" + str(posts))
    for post in posts:
        #print("---------POST-------" + str(post))
        if 'message' in post.keys():
            to_store = form_fb_json(post)
        #    print("--------to_store------" + str(to_store))
            check_no_oid(post,to_store)

            json_blob[str(counter)] = to_store
            counter = counter + 1
            #print ("+++++++++++++++WALLPOST" + post['message'])
        if 'comments' in post.keys():
            for data in post['comments']['data']:
                to_store = form_fb_json(data)
                #print("comments " + to_store)
                check_no_oid(post,to_store)
                json_blob[str(counter)] = to_store
                counter = counter + 1
    return json_blob

getfbposts()