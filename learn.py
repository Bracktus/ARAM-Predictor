import pandas as pd
import numpy as np

"""
We got 2 lists of binary values.
A results column of 1 or 0.

The idea:
We sum all the first lists together
We sum all the second lists together

We now have the frequencies of those champions on a win and a loss
Next we work out p(champ | win) 
And p(champ | loss) 

to predict a teams win/loss:
P(win) * p(champ1 | win) *p(champ2 | win)... * p(champ5(enemy) | win)
and for loss
P(loss) * p(champ1 | loss) *p(champ2 | loss)... * p(champ5(enemy) | loss)

Create a confusion matrix from this
"""

#CSV turns tuples into string so need to do this
df = pd.read_csv("filename.csv", index_col=False, 
				converters={'Friendly Champions': eval, 'Enemy Champions': eval})

#Cleaning up
df.drop_duplicates(subset ="Game ID", keep = "first", inplace = True) 

#One hot encoding the champs
#maximal number
maxF = max(y for x in df['Friendly Champions'] for y in x)
maxE = max(y for x in df['Enemy Champions'] for y in x)

maxO = max(maxF, maxE)

from sklearn.preprocessing import MultiLabelBinarizer

mlb = MultiLabelBinarizer()
df['Friendly Champions'] = (pd.DataFrame(mlb.fit_transform(df['Friendly Champions']),
                  columns=mlb.classes_, 
                  index=df.index)
               .reindex(range(1, maxO+1), axis=1, fill_value=0)
               .to_numpy()
               .tolist())

df['Enemy Champions'] = (pd.DataFrame(mlb.fit_transform(df['Enemy Champions']),
                  columns=mlb.classes_, 
                  index=df.index)
               .reindex(range(1, maxO+1), axis=1, fill_value=0)
               .to_numpy()
               .tolist())

#For now just gonna use the champ data, no FirstBlood, FirstTower or FirstInhib
variables = df.iloc[:,4:-1].values
results = df.iloc[:, -1].values

#Splitting dataset
from sklearn.model_selection import train_test_split
variables_train, variables_test, results_train, results_test = train_test_split(variables, results, test_size = 0.2, random_state = 1)

p_friendly_given_win = np.zeros(len(variables_train[0][0]))
p_enemy_given_win = np.zeros(len(variables_train[0][0]))
p_friendly_given_loss = np.zeros(len(variables_train[0][0]))
p_enemy_given_loss = np.zeros(len(variables_train[0][0]))

p_win = pd.Series(results_train).value_counts()["Win"] / len(results_train)
p_loss = pd.Series(results_train).value_counts()["Fail"] / len(results_train)



for i in range(len(variables_train)):
	if results_train[i] == "Win":
		p_friendly_given_win = p_friendly_given_win + variables_train[i][0]
		p_enemy_given_win = p_enemy_given_win + variables_train[i][1]
	else:
		p_friendly_given_loss = p_friendly_given_loss + variables_train[i][0]
		p_enemy_given_loss = p_enemy_given_loss + variables_train[i][1]

#Calculating the probabilities
p_friendly_given_win /= pd.Series(results_train).value_counts()["Win"]
p_friendly_given_loss /= pd.Series(results_train).value_counts()["Fail"]
p_enemy_given_win /=  pd.Series(results_train).value_counts()["Fail"]
p_enemy_given_loss /= pd.Series(results_train).value_counts()["Fail"]


def predict(team, enemy, p_win, p_loss, p_fw, p_ew, p_fl, p_el):
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

predict_win = []

#Testing the model
for i in range(len(variables_test)):
	team = variables_test[i][0]
	enemy = variables_test[i][1]
	win, lose = predict(team, enemy, p_win, p_loss, p_friendly_given_win,
						p_friendly_given_win, p_friendly_given_loss,
						p_enemy_given_loss)
	if win > lose:
		predict_win.append("Win")
	else:
		predict_win.append("Fail")

def confusion_matrix(prediction, actual):
	true_pos = 0
	true_neg = 0
	false_pos = 0
	false_neg = 0
	
	for i in range(len(prediction)):
		if (prediction[i] == actual[i]) and (prediction[i] == "Win"):
			true_pos+=1
		elif (prediction[i] == actual[i]) and (prediction[i] == "Fail"):
			true_neg+=1
		elif (prediction[i] != actual[i]) and (prediction[i] == "Win"):
			false_pos+=1
		if (prediction[i] != actual[i]) and (prediction[i] == "Fail"):
			false_neg+=1

	return np.array([[true_pos, false_pos],[false_neg, true_neg]])

data = confusion_matrix(predict_win, results_test)

print(f"Recall = {data[0][0]/ (data[0][0] + data[1][0])}")
print(f"Precision = {data[0][0]/(data[0][0] + data[0][1])}")
print(f"Accuracy = {(data[0][0] + data[1][1]) / (data[0][0] + data[0][1] + data[1][0] + data[1][1])}")

print(data)

np.savez('probs.npz',
					p_fw=p_friendly_given_win, 
					p_ew=p_enemy_given_win,
					p_fl=p_friendly_given_loss,
					p_el=p_enemy_given_loss )



