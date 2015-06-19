import tweepy
import re
import requests
import json
import redis
import time
import pymysql
from http.server import BaseHTTPRequestHandler,HTTPServer

consumer_key = "JUNK"
consumer_secret = "JUNK"
access_token = "JUNK"
access_token_secret = "JUNK"

sentiment_url = "http://text-processing.com/api/sentiment/"
NUM_TWEETS = 1
NUM_POSTS = 1
GRAPH_API = 'https://graph.facebook.com/v2.3/flipkart/feed?'
ACCESS_TOKEN = 'JUNK'

username = "root"
password = ""
server = "localhost"
db = pymysql.connect(server, username, password, "sentiment")
cursor = db.cursor()
cursor.connection.autocommit(True)

def sentiment_score(to_analyze):
    payload = {'text': to_analyze}
    r = requests.post(sentiment_url,data=payload)
    if(r.status_code == requests.codes.ok):
        json_data = r.json()
        return json_data

def extract_orderid(tweet_text):
    OD = re.search(r'\sOD[0-9]{18}',tweet_text)
    if(OD == None):
    	return None
    return OD.group(0)

def form_json(tweet, OD, sentiment_json):
    data  = {'tweet': (tweet._json), 'OID': OD, 'sentiment_json':sentiment_json}
    return data

def form_fb_json(post):
    fb_post = {}
    fb_post['text'] = post['message']
    fb_post['user'] = post['from']['name']
    OD = extract_orderid(post['message'])
    sentiment_json = sentiment_score(post['message'])
    data  = {'fbpost': fb_post, 'OID': OD, 'sentiment_json':sentiment_json}
    return data

def gettweets():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)

    search_query = "@flipkart"
    search_query_sachin = "@sachin_bansal"

    results_flipkart = tweepy.Cursor(api.search,q=search_query)
    results_sachinbansal = tweepy.Cursor(api.search,q=search_query_sachin)

    json_blob = {}
    for i,tweet in enumerate(results_flipkart.items(NUM_TWEETS)):
        OD = extract_orderid(tweet.text)
        sentiment_json = sentiment_score(tweet.text)
        to_send = form_json(tweet,OD,sentiment_json)
        json_blob[str(i)]=to_send
    return json_blob

def getfbposts():
    url = GRAPH_API + "access_token=" + ACCESS_TOKEN + "&limit=" + str(NUM_POSTS)
    #print(url)
    r = requests.get(url);
    #print (r.text)
    json_data = json.loads(r.text)
    posts = json_data['data']
    json_blob = {}
    counter = 0
    for post in posts:
        #print("-----------------" + str(i) + "----------------")
        if 'message' in post.keys():
            json_blob[str(counter)] = form_fb_json(post)
            counter = counter + 1
            #print ("+++++++++++++++WALLPOST" + post['message'])
        if 'comments' in post.keys():
            for data in post['comments']['data']:
                json_blob[str(counter)] = form_fb_json(data)
                counter = counter + 1
                #print ("------------COMMENT: " + data['message'])
    return json_blob
    #print(len(posts))

'''
class myHandler(BaseHTTPRequestHandler):
    def do_GET(self) :
        if self.path == "/gettweets" :
            #send response code:
            self.send_response(200)
            #send headers:
            self.send_header("Content-type:", "text/html")
            self.send_headr
            # send a blank line to end headers:
            self.wfile.write(bytes("\n","UTF-8"))
            json_blob = gettweets()
            #send response:
            self.wfile.write(bytes(json.dumps(json_blob),"UTF-8"))
        elif self.path == "/getfbposts" :
             #send response code:
            self.send_response(200)
            #send headers:
            self.send_header("Content-type:", "text/html")
            # send a blank line to end headers:
            self.wfile.write(bytes("\n","UTF-8"))
            json_blob = getfbposts()
            #send response:
            self.wfile.write(bytes(json.dumps(json_blob),"UTF-8"))'''

def fb_push(fb_dump):
    facebook_key = "fb_data" + time.strftime("%X")
    query = "insert into facebook_sentiment(fb_key, fb_value) values('%s', '%s')"%(facebook_key, json.dumps(fb_dump))
    #print(query)
    #print("fbdump="+str(fb_dump)+str(type(fb_dump)))
    cursor.execute(query)


def tw_push(tw_dump):
    tw_key = "tw_data" + time.strftime("%X")
    query = "insert into twitter_sentiment(tw_key, tw_value) values('%s', '%s')"%(tw_key, json.dumps(tw_dump))
    #print(query)
    #print("twdump="+str(tw_dump)+str(type(tw_dump)))
    cursor.execute(query)

def main():
    #server = HTTPServer(("localhost", 8003), myHandler)
    #server.serve_forever()

    fb_dumps = getfbposts()
    #print(fb_dumps)
    for k,v in fb_dumps.items():
        fb_push(v)

    tw_dumps = gettweets()
    #print(tw_dumps)
    for k,v in tw_dumps.items():
        tw_push(v)

if __name__ == '__main__':
    main()
