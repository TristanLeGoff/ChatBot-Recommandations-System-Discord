# import
import os
import random
import nltk
nltk.download('wordnet')
import re
from nltk.corpus import wordnet
import discord
from dotenv import load_dotenv
import wikipedia
import numpy as np
import pandas as pd
from fuzzywuzzy import process

wikipedia.set_lang("en")
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
client = discord.Client()

#Import the corrMatrix
corrMatrix = pd.read_pickle(r"corrMatrix.pkl")
gameList = corrMatrix.index

def closestGame(mystring):
    highest = process.extractOne(mystring,gameList)
    return highest

def recomandGame(myGameList):
    myRatings = pd.DataFrame(columns=['game', 'rating'])
    for game in myGameList:
        myRatings = myRatings.append({'game':game, 'rating':5}, ignore_index=True)
    myRatings = myRatings.set_index('game')
    similar_candidates = pd.Series(dtype='float64')
    for i in range(0, len(myRatings.index)):
        # retrieve similar games to this one that I rated
        similar_movies = corrMatrix[myRatings.index[i]].dropna()
        # scale its similarity by how well I rated this game
        similar_movies = similar_movies.map(lambda x: x * myRatings.iloc[i]['rating'])
        # add the score to the list of similar candidates
        similar_candidates = similar_candidates.append(similar_movies)
        
    similar_candidates = similar_candidates.groupby(similar_candidates.index).sum()
    similar_candidates = similar_candidates.drop(similar_candidates.loc[similar_candidates.index.isin(myRatings.index)].index)

    similar_candidates.sort_values(inplace = True, ascending = False)
    similar_candidates = similar_candidates[0:10].index
    return similar_candidates

# Building a list of Keywords
list_words=['hello','help','information','like','know','thank','thanks','time','day','weather','movie']
list_syn={}

for word in list_words:
    synonyms=[]
    for syn in wordnet.synsets(word):
        for lem in syn.lemmas():
            # Remove any special characters from synonym strings
            lem_name = re.sub('[^a-zA-Z0-9 \n\.]', ' ', lem.name())
            synonyms.append(lem_name)
    list_syn[word]=set(synonyms)
# print (list_syn)

# Building dictionary of Intents & Keywords
keywords={}
keywords_dict={}


# Defining a new key in the keywords dictionary

keywords['greet']=[]
for synonym in list(list_syn['hello']):
    keywords['greet'].append('.*\\b'+synonym+'\\b.*')

keywords['help']=[]
for synonym in list(list_syn['help']):
    keywords['help'].append('.*\\b'+synonym+'\\b.*')

keywords['info']=[]
for synonym in list(list_syn['information']):
    keywords['info'].append('.*\\b'+synonym+'\\b.*')

keywords['like']=[]
for synonym in list(list_syn['like']):
    keywords['like'].append('.*\\b'+synonym+'\\b.*')

keywords['know']=[]
for synonym in list(list_syn['know']):
    keywords['know'].append('.*\\b'+synonym+'\\b.*')

keywords['thank']=[]
for synonym in list(list_syn['thank']):
    keywords['thank'].append('.*\\b'+synonym+'\\b.*')

keywords['thanks']=[]
for synonym in list(list_syn['thanks']):
    keywords['thanks'].append('.*\\b'+synonym+'\\b.*')

keywords['time']=[]
for synonym in list(list_syn['time']):
    keywords['time'].append('.*\\b'+synonym+'\\b.*')

keywords['day']=[]
for synonym in list(list_syn['day']):
    keywords['day'].append('.*\\b'+synonym+'\\b.*')

keywords['weather']=[]
for synonym in list(list_syn['weather']):
    keywords['weather'].append('.*\\b'+synonym+'\\b.*')

keywords['movie']=[]
for synonym in list(list_syn['movie']):
    keywords['movie'].append('.*\\b'+synonym+'\\b.*')


keywords['feelings']=[]
keywords['feelings'].append('.*\\bhow are\\b.*')


for intent, keys in keywords.items():
    # Joining the values in the keywords dictionary with the OR (|) operator updating them in keywords_dict dictionary
    keywords_dict[intent]=re.compile('|'.join(keys))
# print (keywords_dict)

help_text = '\n\
    !info {video-game} -> Give information on the video games you typed\n\
    !add {video-game} -> Add the video game you typed to your favorite list\n\
    !fav -> Display your favorite video games list\n\
    !clear -> Clear your favorite video games list\n\
    !recommandation -> Recomand you 10 video games that you might like depending your favorite list'

responses={
    'greet':'Hello! How can I help you?',
    'help':'If it can help you, here are my commands :\n'+help_text,    
    'info':'The only information i have is the list of my commands :\n'+help_text,
    'feelings':'I am fine thanks',
    'like':'I do not know if this is what you would like but I have these commands:\n'+help_text,
    'know':'I do not know if this is what you want to know but I have these commands:\n'+help_text,
    'thank':'You are welcome',
    'thanks':'You are welcome',
    'time':'I have no idea about time but I may be one on video games (type "help")',
    'day':'I have no idea about day but I may be one on video games (type "help")',
    'weather':'You are not on the good week, that is not the weather bot (type "help")',
    'movie':'You are not on the good week, that is not the movie bot (type "help")',
    'fallback':'I dont quite understand. Could you repeat that, or type "help".',
}

# global var
allFavList = {}

@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')

@client.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
        f'Hi {member.name}, welcome to my Discord server!'
    )

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    global allFavList
    global tempGame

    if message.content[0:5] == '!info':
        if message.content[6:] == "dota 2" or message.content[6:] == "Dota 2":
            response = wikipedia.summary("dotq 2", sentences=3)
        else:
            response = wikipedia.summary(message.content[6:], sentences=3)

    elif message.content[0:4] == '!add':
        myclose = closestGame(message.content[5:])
        if myclose[1]>95:
            if message.author.name in allFavList:
                if myclose[0] not in allFavList[message.author.name]:
                    allFavList[message.author.name].append(myclose[0])
            else :
                allFavList[message.author.name]=[myclose[0]]
            response = "The game '"+myclose[0]+"' was added to your favorite list"
        else:
            tempGame = myclose[0]
            response = "I am not sure that I have this game in my model, the closest game is : '"+myclose[0]+"', If you want to add it to your list type '!yes' or try another game"

    elif message.content[0:4] == '!fav':
        if message.author.name in allFavList:
            response = 'This is your favorite list of video games : \n'
            for game in allFavList[message.author.name]:
                response = response+game+', '
            if len(allFavList[message.author.name]) == 0:
                response = "Your favorite list is empty (use '!add {video games}')"
        else:
            response = "Your favorite list is empty (use '!add {video games}')"

    elif message.content[0:6] == '!clear':
        if message.author.name in allFavList:
            allFavList[message.author.name]=[]
        response = "your favorites list has been successfully emptied"

    elif message.content[0:15] == '!recommandation':
        if message.author.name in allFavList:
            if len(allFavList[message.author.name])>0:
                myRec = recomandGame(allFavList[message.author.name])
                if len(myRec)<10:
                    response = 'Sorry but I do not have enough information about you to suggest games to you, try adding more popular games to your favorite list'
                else:
                    response = 'Thanks to your favorite list, I offer you video games that you might like: \n'
                    i = 0
                    for game in myRec:
                        i += 1
                        response = response + str(i) + ". " + game + "\n"

            else :
                response = "First you have to add video games to your favorite list (use '!add {video games}')"
        else:
            response = "First you have to add video games to your favorite list (use '!add {video games}')"
    
    elif message.content[0:4] == '!yes':
        if message.author.name in allFavList:
            if tempGame not in allFavList[message.author.name]:
                allFavList[message.author.name].append(tempGame)
        else :
            allFavList[message.author.name]=[tempGame]
        response = "The game '"+tempGame+"' was added to your favorite list"

    elif message.content[0:5] == '!test':
        response = str(message.author.name)

    else:
        user_input = message.content.lower()
        matched_intent = None 
        for intent,pattern in keywords_dict.items():
            # Using the regular expression search function to look for keywords in user input
            if re.search(pattern, user_input): 
                # if a keyword matches, select the corresponding intent from the keywords_dict dictionary
                matched_intent=intent  

        # The fallback intent is selected by default
        key='fallback' 
        if matched_intent in responses:
            # If a keyword matches, the fallback intent is replaced by the matched intent as the key for the responses dictionary
            key = matched_intent 

        response = responses[key]

    # response = wikipedia.summary(message.content, sentences=3)
    # response = message.content[0:4]
    await message.channel.send(response)

client.run(TOKEN)