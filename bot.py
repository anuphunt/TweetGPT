import tweepy
import json
import schedule
import time
from jsonReader import read

from gpt3 import generate_reply

creds = read('config.json')

# auth = tweepy.OAuthHandler(consumer_key="sRDEjgJXnnqQ57EEkA73g2sGX",
#                            consumer_secret="3WE6Ouj80YwWiJVQK3lrWNUGXIABARNYTYia5kHWwxCTT2MB2R")
# auth.set_access_token("1613040771980234752-uJSBEhQ3PlRyyKcnPJH0Yfhx9dn5Vf",
#                       "w0B0FukhXc4Mu0wXjf36BZAavJ7uEpqZtKidjyLngOtde")

auth = tweepy.OAuthHandler(consumer_key=creds['twitter']['consumer_key'],
                           consumer_secret=creds['twitter']['consumer_secret'])
auth.set_access_token(creds['twitter']['access_token_key'],
                      creds['twitter']['access_token_secret'])
api = tweepy.API(auth)

hashtag = creds['hashtag']

exclude_keywords_in_username = ["bot", "alert", "telegram", "tracker"]


def from_creator(tweet):
    if hasattr(tweet, "retweeted_status"):
        return False
    elif tweet.in_reply_to_status_id != None:
        return False
    elif tweet.in_reply_to_screen_name != None:
        return False
    elif tweet.in_reply_to_user_id != None:
        return False
    else:
        return True


def get_status(tweet):
    if tweet.truncated:
        return api.get_status(tweet.id, tweet_mode="extended").full_text


tweets_and_replies = []


def reply_to_tweet(reply, id):
    api.update_status(status=reply, in_reply_to_status_id=id,
                      auto_populate_reply_metadata=True)

# follow original poster of the tweet


def follow_op(screen_name):
    if (screen_name and len(screen_name) > 0):
        api.create_friendship(screen_name=screen_name)


def append_to_file(status, reply):
    tweets_and_replies.append(
        "----------------------------------------------------------------------\n")
    tweets_and_replies.append("Tweet: " + status + "\n")
    tweets_and_replies.append("Reply: " + reply + "\n")
    tweets_and_replies.append(
        "----------------------------------------------------------------------\n")


def log(status, reply):
    print("Original Tweet: " + status)
    print("Reply: " + reply)


def run_tweet_reply():
    print("RUNNING THE JOB......")
    tweets = tweepy.Cursor(api.search_tweets, q=hashtag,
                           result_type="popular", lang="en").items(40)

    # With geocode
    # tweets = tweepy.Cursor(api.search_tweets, q=hashtag, result_type="recent", lang="en", geocode="46.9442348,-122.6313824,5000mi").items(5)
    generated_reply_count = 0

    with open("tweet_ids.txt", "r+") as ids_file:
        saved_ids = set(map(str.strip, ids_file.readlines()))

        for tweet in tweets:
            status = get_status(tweet) if tweet.truncated else tweet.text
            if from_creator(tweet) == True:
                if any(keyword not in tweet.user.name.lower() for keyword in exclude_keywords_in_username):
                    if str(tweet.id) not in saved_ids:
                        try:
                            reply = generate_reply(status)
                            saved_ids.add(str(tweet.id))
                            reply_to_tweet(reply, tweet.id)
                            follow_op(tweet.user.screen_name)
                            append_to_file(status, reply)
                            log(status, reply)
                            generated_reply_count += 1
                            # Do not generate more than 5 replies in one hour.
                            if (generated_reply_count > 5):
                                print("Reply limit reached.")
                                break
                        except Exception:
                            print("Some error occured. Trying again!")
                            continue
                    else:
                        print("Already replied to this tweet.")
            else:
                print("This is not original tweet.")
        ids_file.seek(0)
        for id in saved_ids:
            ids_file.write(id+"\n")

    with open("tweet_replies.txt", "w") as tr:
        tr.writelines(tweets_and_replies)

    print("FINISHED JOB")


run_tweet_reply()
schedule.every(1).hours.do(run_tweet_reply)

while True:
    schedule.run_pending()
    time.sleep(1)
