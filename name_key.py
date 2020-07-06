#For champ IDs
import urllib.request, json 
import numpy as np
#from learn import predict

with urllib.request.urlopen("http://ddragon.leagueoflegends.com/cdn/10.13.1/data/en_US/champion.json") as url:
    champJson = json.loads(url.read().decode())
 

def predict(team, enemy, p_win, p_loss, p_fw, p_ew, p_fl, p_el):
#Copied over from the other file
	teamList = []
	enemyList = []
	for i in range(len(team)):
		if team[i]:
			teamList.append(i)
		if enemy[i]:
			enemyList.append(i)

	teamWin = p_win
	teamLose = p_loss

	for fChamp in teamList:
		teamWin = teamWin * p_fw[fChamp]
		teamLose = teamLose * p_fl[fChamp]
	for eChamp in enemyList:
		teamWin = teamWin * p_ew[eChamp]
		teamLose = teamLose * p_el[eChamp]

	return teamWin, teamLose

def name_to_key(name, data):
	for i in data["data"]:
		if i == name:
			return int(data["data"][i]["key"])
	return -1

def key_to_name(key, data):
	for i in data["data"]:
		if data["data"][i]["key"] == str(key):
			return data["data"][i]["name"]
	return "None"

def print_all_names(data):
	for i in data["data"]:
		print(i)


data = np.load('probs.npz')

p_fw = data["p_fw"]
p_ew = data["p_ew"] 
p_fl = data["p_fl"]
p_el = data["p_el"]

print("Welcome to the ARAM predictor")
print("Please enter champ names with no punctuation and add a space if needed :)")
friendly_champs = []
enemy_champs = []

for i in range(5):
	champ_name = input("Enter a champion on your team \n")
	champ_name = "".join([i.capitalize() for i in champ_name.split()])
	champ_key = name_to_key(champ_name, champJson)
	while champ_key == -1:
		champ_name = input("Champ not recognized, try again \n")
		champ_name = "".join([i.capitalize() for i in champ_name.split()])
		champ_key = name_to_key(champ_name, champJson)

	friendly_champs.append(champ_key)

for i in range(5):
	champ_name = input("Enter a champion on your enemy's team \n")
	champ_name = "".join([i.capitalize() for i in champ_name.split()])
	champ_key = name_to_key(champ_name, champJson)
	while champ_key == -1:
		champ_name = input("Champ not recognized, try again \n")
		champ_name = "".join([i.capitalize() for i in champ_name.split()])
		champ_key = name_to_key(champ_name, champJson)

	enemy_champs.append(champ_key)

friendly_champs_bin = [(1 if i in friendly_champs else 0) for i in range(1, max(friendly_champs)+1)] 
enemy_champs_bin = [(1 if i in friendly_champs else 0) for i in range(1, max(friendly_champs)+1)] 

win, lose = predict(friendly_champs_bin, enemy_champs_bin, 0.5, 0.5, p_fw, p_ew, p_fl, p_el)

print([key_to_name(i, champJson) for i in friendly_champs])
print([key_to_name(i, champJson) for i in enemy_champs])

if win > lose:
	print("I think you will win")
else:
	print("I think you will lose")