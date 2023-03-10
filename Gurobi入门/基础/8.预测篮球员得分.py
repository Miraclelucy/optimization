import pandas as pd                                       #importing pandas
import numpy as np                                        #importing numpy
import matplotlib.pyplot as plt                           #importing matplotlib
import seaborn as sns                                     #importing seaborn
from sklearn.model_selection import train_test_split      #importing scikit-learn's function for data splitting
from sklearn.linear_model import LinearRegression         #importing scikit-learn's linear regressor function
from sklearn.neural_network import MLPRegressor           #importing scikit-learn's neural network function
from sklearn.ensemble import GradientBoostingRegressor    #importing scikit-learn's gradient booster regressor function
from sklearn.metrics import mean_squared_error            #importing scikit-learn's root mean squared error function for model evaluation
from sklearn.model_selection import cross_validate        #improting scikit-learn's cross validation function
from gurobipy import Model, GRB, quicksum                 #importing Gurobi

boxscores = pd.read_csv('boxscores_dataset.csv')     #load boxscores dataset
boxscores = boxscores[(boxscores.playMin>=3) | (boxscores.playMin.isnull())]

fig, (FGA, FGM, FTM, Min) = plt.subplots(1, 4, figsize=(14,5))
fig.tight_layout()

FGA.scatter(boxscores['playFGA'], boxscores['FantasyPoints'], c='blue', alpha = .2)
FGM.scatter(boxscores['playFGM'], boxscores['FantasyPoints'], c='lightblue', alpha = .2)
FTM.scatter(boxscores['playFTM'], boxscores['FantasyPoints'], c='coral', alpha = .2)
Min.scatter(boxscores['playMin'], boxscores['FantasyPoints'], c='purple', alpha = .2)

FGA.set_xlabel('Field Goal Attempts')
FGM.set_xlabel('Field Goals Made')
FTM.set_xlabel('Free Throws Made')
Min.set_xlabel('Minutes Played')

FGA.set_ylabel('Fantasy Points')
plt.show()

hplot = sns.histplot(boxscores['FantasyPoints'], color="blue", label="Fantasy Points", kde=True, stat="density", linewidth=0, bins=20)
hplot.set_xlabel("Fantasy Points", fontsize = 12)
hplot.set_ylabel("Density", fontsize = 12)
sns.set(rc={"figure.figsize":(14, 5)})
plt.show()

horizon=3

# ???????????????
for column_name in ['playPTS','playAST','playTO','playSTL','playBLK',
                    'playTRB','playFGA','playFTA','play2P%','play3P%',
                    'playFT%','playMin','teamDayOff','FantasyPoints']:
    boxscores['moving' + column_name] = boxscores.groupby(['playDispNm'])[column_name].transform(lambda x: x.rolling(horizon, 1).mean().shift(1))

boxscores.dropna(subset = ["movingplayPTS"], inplace=True)

# ??????????????????????????????????????????????????????????????????????????????
sns.set(rc = {'figure.figsize':(15,8)})
sns.heatmap(boxscores[['movingplayPTS', 'movingplayAST','movingplayTO','movingplaySTL','movingplayBLK',
                       'movingplayTRB','movingplayFGA','movingplayFTA','movingplay2P%','movingplay3P%',
                       'movingplayFT%','movingplayMin','movingteamDayOff','movingFantasyPoints']].corr(),annot=True)
plt.show()

# ???2?????????
boxscores['dummyTeamLoc'] = pd.get_dummies(data=boxscores['teamLoc'],drop_first=True)    #?????????????????????????????????
boxscores['dummyplayStat'] = pd.get_dummies(data=boxscores['playStat'],drop_first=True)  #??????????????????????????????

forecasting_data = boxscores[boxscores.gmDate != '2017-12-25']  #for model training, we exclude observation on December 25, 2017

X = forecasting_data[['movingplayAST','movingplayTO','movingplaySTL','movingplayBLK','movingplayTRB',
                      'movingplayFTA','movingplayFT%','dummyplayStat']]  #select the features that will be used for model training
y = forecasting_data['FantasyPoints']  #target set
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=4)      #dataset splitting

# ???3????????????????????????
linear_regressor = LinearRegression()                                                         #load linear regressor
linear_regressor.fit(X_train, y_train)                                                        #train the linear regression model
linear_regression_validation = cross_validate(linear_regressor, X_train, y_train, cv=5, return_train_score=True, return_estimator=True)

mlp = MLPRegressor(hidden_layer_sizes=(5,5), activation='relu')                               #load neural network
mlp.fit(X_train,y_train)                                                                      #train the neural network with a ReLU function and two hidden layers with 5 nodes each
mlp_validation = cross_validate(mlp, X_train, y_train, cv=5, return_train_score=True, return_estimator=True)

gb = GradientBoostingRegressor()                                                              #load a gradient boosting regressor
gb.fit(X_train, y_train)                                                                      #train a gradient boosting model
gb_validation = cross_validate(gb, X_train, y_train, cv=5, return_train_score=True, return_estimator=True)

# ??????
linear_regression_predictions = linear_regressor.predict(X_test)                              #make predictions based on the test set for the linear regression model
mlp_predictions = mlp.predict(X_test)                                                         #make predictions based on the test set for the neural network model
gb_predictions = gb.predict(X_test)                                                           #make predictions based on the test set for the gradient boosting model

# ????????????????????? MSE??????
linear_regression_mse = mean_squared_error(y_test, linear_regression_predictions)             #calculate the MSE for the linear regression model
mlp_mse = mean_squared_error(y_test, mlp_predictions)                                         #calculate the MSE for the neural network model
gb_mse = mean_squared_error(y_test, gb_predictions)                                           #calculate the MSE for the gradient boosting model

results = {'Linear Regression':[linear_regression_mse],'ReLU Neural Network':[mlp_mse],'Gradient Boosting Regressor':[gb_mse]}
modeling_results = pd.DataFrame(data=results,index=['MSE'])

print(modeling_results)

# ??????????????????????????????????????????
# ??????????????????????????????????????????????????????'2017-12-25'??????????????????????????????????????????
gb_final = GradientBoostingRegressor(random_state=4)
gb_final.fit(X, y)

optimization_dataset = boxscores
optimization_dataset['PredictedFantasyPoints'] = gb_final.predict(boxscores[['movingplayAST','movingplayTO'
    ,'movingplaySTL','movingplayBLK','movingplayTRB','movingplayFTA','movingplayFT%','dummyplayStat']])

player_results = pd.read_csv('target_games.csv')
player_list = list(player_results['Player'].unique())
col = pd.DataFrame()

for player in player_list:
    optimization_data_per_player = optimization_dataset.loc[(optimization_dataset['playDispNm']==player)&(optimization_dataset['gmDate']=='2017-12-25')]
    col = col.append(optimization_data_per_player)

player_results['PredictedFantasyPoints'] = col['PredictedFantasyPoints'].values

# ?????????/??????????????? Points/Salary Ratio
pd.set_option('display.expand_frame_repr', False)
player_results['Points/Salary Ratio'] = 1000*player_results['PredictedFantasyPoints']/player_results['Salary']    #we multiple the fantasy vs salary ratio by 1000 for better visualization
player_results.sort_values(by='PredictedFantasyPoints',ascending=False).head(5)

#?????????????????????????????????PG/SG/SF/PF/C,???????????????????????? ???player_list???????????????24???PG/22???SG/22???SF/19???PF/9???C?????????24*22*22*19*9=1986336?????????
# a point guard (PG), a shooting guard (SG), a small forward (SF), a power forward (PF), and a center (C)

indices = player_results.Player
points = dict(zip(indices, player_results.PredictedFantasyPoints))
salaries = dict(zip(indices, player_results.Salary))
S = 30000

m = Model()       # this defines the model that we'll add to as we finish the formulation
# ??????????????????96????????????????????????
y = m.addVars(indices, vtype=GRB.BINARY, name="y")

m.setObjective(quicksum(points[i]*y[i] for i in indices), GRB.MAXIMIZE)

# ?????????????????????????????????????????????1???
player_position_map = list(zip(player_results.Player, player_results.Pos))
for j in player_results.Pos:
    m.addConstr(quicksum([y[i] for i, pos in player_position_map if pos==j])==1)

# ????????????????????????????????????????????????????????????3???
m.addConstr(quicksum(salaries[i]*y[i] for i in indices) <= S, name="salary")

# ?????????????????????
m.optimize()

# ??????????????????
results = pd.DataFrame()

for v in m.getVars():
    if v.x > 1e-6:
        results = results.append(player_results.iloc[v.index][['Player','Pos','PredictedFantasyPoints','Salary']])
        print(v.varName, v.x)

print('Total fantasy score: ', m.objVal)

results['True Fantasy Points'] = [53.5,17.25,28.5,15.5,29.25]
print(results)
