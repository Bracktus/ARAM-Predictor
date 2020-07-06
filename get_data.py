import time, os, json, csv, pickle
import requests
import pandas as pd
import config

#Do not proccess the JSON. Do that later as it'll slow down data collection
#Maybe filter for aram games coz some people only play aram which'll help

"""
PLAN:
1.)Crawl through MY match hist
2.)Get all aram games
3.)Look at everyone who was in the game, if i've seen before: ignore
										 else: add to list of players
4.)Crawl through player's aram match hist
5.)Repeat
"""

MY_TOKEN = config.token
HEADERS = { "X-Riot-Token": MY_TOKEN }
startingName = "bracktus"

def getAccIDFromUsername(username):
	"""Gets an account ID from a username. Used as a starting point"""
	url_for_name = f"https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{username}"
	r_name = requests.get(url_for_name, headers=HEADERS)
	userData = json.loads(r_name.text)
	return userData["accountId"]

def getMatchIDsFromAccID(accID, old_accounts, new_accounts):
	"""This returns the matchIDs of the last 150 games that someone played"""

	#Getting my match history IDs (last 100 games)
	url_for_match_hist = f"https://euw1.api.riotgames.com/lol/match/v4/matchlists/by-account/{accID}"
	r_match_hist = requests.get(url_for_match_hist, headers=HEADERS)
	if "status" in json.loads(r_match_hist.text):
		return None
	else:
		print(json.loads(r_match_hist.text))


	#Parsing json to get gameId 
	match_ID_list = []
	matchHistory = json.loads(r_match_hist.text)
	for i in range(len(matchHistory["matches"])):
		match_ID_list.append(matchHistory["matches"][i]["gameId"])

	old_accounts.append(accID)
	print(old_accounts)

	return match_ID_list

def getMatchDatafromMatchID(matchID):
	"""This returns the match data from a matchID"""
	url_for_match_data = "https://euw1.api.riotgames.com/lol/match/v4/matches/"
	r_match_data = requests.get(url_for_match_data + str(matchID), headers=HEADERS)
	match_data = json.loads(r_match_data.text)
	try:
		#Handling Gateway timeouts
		if match_data["gameMode"] == "ARAM":
			#Only returning ARAM games
			return match_data
		else:
			return None
	except:
		print("Error Scraping Data")
		return None

def getFeaturesFromMatchData(match_data, df):
	game_Id = match_data["gameId"]
	first_Blood = match_data["teams"][0]["firstBlood"]
	first_Tower = match_data["teams"][0]["firstTower"]
	first_Inhib = match_data["teams"][0]["firstInhibitor"]
	win = match_data["teams"][0]["win"]


	team_champ_list = []
	enemy_champ_list = []

	for i in range(5):
		team_champ_list.append(match_data['participants'][i]['championId'])
	for k in range(5,10):
		enemy_champ_list.append(match_data['participants'][k]['championId'])

	
	df.loc[len(df)] = [game_Id, first_Blood, first_Tower, first_Inhib, tuple(team_champ_list)
					   ,tuple(enemy_champ_list), win]
	return df

def newAccountFinder(match_data, new_accounts, old_accounts):
	for i in match_data["participantIdentities"]:
		#Getting accounts to crawl through
		account = i["player"]["accountId"]
		if account not in old_accounts:
			new_accounts.append(account)

columns = ["Game ID", "First Blood", "First Tower", "First Inhibitor",
		   "Friendly Champions", "Enemy Champions", "Game Won"]

beginning = 0
end = 0
new_accounts = []
old_accounts = []

accId = getAccIDFromUsername("Skhym")
new_accounts.append(accId)
df = pd.DataFrame(columns=columns)

for i in range(500):
	#Go through ~500 accounts most likely less
	if new_accounts[i] not in old_accounts:
		match_ID_list = getMatchIDsFromAccID(new_accounts[i], old_accounts, new_accounts)
		#sorry idk what i'm doing here
		if match_ID_list == None:
			continue
	else:
		continue
		#loop back to top 
	for matchID in match_ID_list:
		#for every match from one account
		time.sleep(2.1) #Need this line to not get banned by riot (100 Reqs / 2 mins)
		match_data = getMatchDatafromMatchID(matchID)
		if match_data:
			#If it's an aram game
			if len(new_accounts) < 500:
				newAccountFinder(match_data, new_accounts, old_accounts)
			getFeaturesFromMatchData(match_data, df)

	end = len(df)
	# if file does not exist write header 
	if not os.path.isfile('filename.csv'):
		df.to_csv('filename.csv', header='column_names',index=False)
	else: # else it exists so append without writing the header
		df[beginning:end].to_csv('filename.csv', mode='a', header=False,, index=False)
		beginning = end
