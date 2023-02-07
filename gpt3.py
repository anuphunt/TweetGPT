import openai
from jsonReader import read

creds = read('config.json')
openai.api_key = creds['openai']['api_key']


def generate_reply(tweet):
    prompt = "Write a reply for this tweet: \n" + str(tweet)
    # Generate a reply
    response = openai.Completion.create(
        engine="text-davinci-002", prompt=prompt, max_tokens=100)

    print(response)

    return response["choices"][0]["text"]
