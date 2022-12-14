import requests
import json
import pandas as pd
from requests_oauthlib import OAuth1Session
from collections import OrderedDict
from dotenv import load_dotenv
import os
import datetime as dt

load_dotenv()

class Twitter():
  def __init__(self):
    self.key = os.getenv('KEY')
    self.secret = os.getenv('SECRET')
    self.token = os.getenv('TOKEN')
    self.oauth = self.init_twitter()
    self.user = os.environ['USER']
    self.usr_id = self.get_user_id(self.user)

  def init_twitter(self):
    request_token_url = "https://api.twitter.com/oauth/request_token"
    oauth = OAuth1Session(self.key, client_secret=self.secret)

    try:
        fetch_response = oauth.fetch_request_token(request_token_url)
    except ValueError:
        print(
            "There may have been an issue with the consumer_key or consumer_secret you entered."
        )

    resource_owner_key = fetch_response.get("oauth_token")
    resource_owner_secret = fetch_response.get("oauth_token_secret")

    # Get authorization
    base_authorization_url = "https://api.twitter.com/oauth/authorize"
    authorization_url = oauth.authorization_url(base_authorization_url)
    print("Please go here and authorize: %s" % authorization_url)
    verifier = input("Paste the PIN here: ")

    # Get the access token
    access_token_url = "https://api.twitter.com/oauth/access_token"

    oauth = OAuth1Session(
        self.key,
        client_secret=self.secret,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
        verifier=verifier,
    )
    oauth_tokens = oauth.fetch_access_token(access_token_url)

    access_token = oauth_tokens["oauth_token"]
    access_token_secret = oauth_tokens["oauth_token_secret"]

    oauth = OAuth1Session(
      self.key,
      client_secret=self.secret,
      resource_owner_key=access_token,
      resource_owner_secret=access_token_secret,)
    
    return oauth

  # --- --- ---

  # Retorna DataFrame contendo o ID do usu??rio
  def get_user_id(self, username):
    response = json.loads(self.oauth.get(f"https://api.twitter.com/2/users/by?usernames={username}").text)

    return response['data'][0]['id']

  # Retorna DataFrame contendo os ??ltimos 300 tweets do usu??rio
  def get_tweets(self):
    max = 100
    url = f'https://api.twitter.com/2/users/{twitter.usr_id}/tweets?tweet.fields=created_at&max_results={max}&exclude=replies'#'#&start_time={data_inicial}'#&end_time={data_final}'

    response = json.loads(twitter.oauth.get(url).text)

    if 'next_token' in response['meta'].keys():
      json_final = []
      next_token = response['meta']['next_token']

      while 'next_token' in response['meta'].keys():
        url = f'https://api.twitter.com/2/users/{twitter.usr_id}/tweets?tweet.fields=created_at&max_results={max}&exclude=replies&pagination_token={next_token}'
        response = json.loads(twitter.oauth.get(url).text)
        json_final.append(response['data'])
        next_token = response['meta']['next_token']

      df = pd.DataFrame([item for sublist in json_final for item in sublist])

    df = pd.DataFrame(response['data'])
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['created_at'] -= dt.timedelta(hours=3) # GMT-03:00
    df['permalink'] = [f'https://twitter.com/{twitter.user}/status/{x}' for x in df['id']]

    return df


  # Retorna DataFrame contendo m??tricas p??blicas e n??o-p??blicas dos tweets inputados
  def get_metrics(self, ids):
    dict_metrics = OrderedDict()

    response = json.loads(self.oauth.get(f'https://api.twitter.com/2/tweets?ids={ids}&tweet.fields=public_metrics,non_public_metrics').text)

    for tweet in response['data']:
      dict_metrics[tweet['text']] = dict(tweet['public_metrics'], **tweet['non_public_metrics'])

    df_metrics = pd.DataFrame(dict_metrics.values())
    df_keys = pd.DataFrame(dict_metrics.keys())

    df_metrics = df_metrics.reset_index()
    df_keys = df_keys.reset_index()

    df_final = df_metrics.merge(df_keys, on='index')
    df_final.rename(columns={0: 'tweet'}, inplace=True)
    df_final.drop('index', axis=1, inplace=True)

    return df_final
