from bs4 import BeautifulSoup
import requests

def getSoup(url):
    response = requests.get(url)
    html = BeautifulSoup(response.text, 'html.parser')
    return html

def getTotals(team):
    categories = ["g", "mp", "fg", "fga", "fg_pct", "fg3", "fg3a", "fg3_pct", "ft", "fta", "ft_pct", "trb", "ast", "stl", "blk", "tov", "pts"]
    scoring = {"fg": 1, "fga": -1, "ft": 1, "fta": -1, "trb": 1.2, "ast": 1.5, "stl": 3, "blk": 3, "tov": -1, "pts": 1}

    html = getSoup(seasonurl)

    rows = html.find('tbody').findAll('tr', {'class': 'full_table'})

    stats = []
    for row in rows:
        name = row.find('td').find('a').text
        if name in team: # if player is on team
            fpts = 0
            player = {'name': name} # insert player name

            for cat in categories:
                val = row.find('td', {'data-stat': cat}).text
                if val == "":
                    val = 0
                else:
                    player[cat] = float(val) # insert stats under category
                
                if cat in scoring.keys(): # if category is scored
                    fpts += scoring[cat] * player[cat] # add to total
            player['fpts'] = fpts

            stats.append(player)
    return stats

def averageStats(team):
    stats = getTotals(team)
    doNotAvg = ('g', 'fg_pct', 'fg3_pct', 'ft_pct')
    averages = []
    for player in stats:
        copy = {}
        for key in player.keys():
            copy[key] = player[key]
            if key != 'name' and key not in doNotAvg:
                copy[key] /= player['g']
        averages.append(copy)
    return averages

def gameLog(player):
    html = getSoup(seasonurl)

    rows = html.find('tbody').findAll('tr', {'class': 'full_table'})

    for row in rows:
        nameLink = row.find('td', {'data-stat': 'player'}).find('a')
        if nameLink.text == player:
            playerLink = nameLink['href'].replace('.html', "")
    
    gamesPage = f"https://www.basketball-reference.com{playerLink}/gamelog/2020"

    html = getSoup(gamesPage)

    rows = html.find('tbody').findAll('tr')

    stats = []
    for row in rows:
        date = row.find('td', {'data-stat': 'date_game'}).text
        player = {'date': date}
        
        fpts = 0
        played = True
        for cat in categories[1:]:
            cell = row.find('td', {'data-stat': cat})
            if cell == None: # player is out, has no stats
                played = False
                player['mp'] = row.find('td', {'data-stat': 'reason'}).text
                break # move to next game
            else: 
                player[cat] = cell.text

            if player[cat] != "" and cat != 'mp':
                player[cat] = float(player[cat]) # cast all values to float if possible
            elif cat != 'mp':
                player[cat] = 0
            
            if cat in scoring.keys(): # if category is scored
                fpts += scoring[cat] * player[cat] # add to total

        if played == True:
            player['fpts'] = fpts

        stats.append(player)

    return stats        


def printStats(stats):
    for key in stats[0].keys(): # arbitrary player stat categories
        if key == 'name':
            print(f"{key:30}", end="")
        elif key == 'date':
            print(f"{key:15}", end="")
        else:
            print(f"{key:<8}", end="")
    print()

    for player in stats:
        for key in player.keys():
            if key == 'name':
                print(f"{player[key]:30}", end="")
            elif key == 'date':
                print(f"{player[key]:15}", end="")
            else:
                if key != 'mp':
                    print(f"{player[key]:<8.3f}", end="")
                else:
                    print(f"{player[key]:<8}", end="")
        print()

def getTeams(json):
    return [[player['playerPoolEntry']['player']['fullName'] for player in team['roster']['entries']] for team in fantasy['teams']]

class League:
    name = ""
    teams = []
    scoring = {}

    def __init__(self, url):
        swid = '{2C5C7745-8766-42EC-A3F1-7A0B7B109444}'
        espn_s2 = 'AECmhjRVqnP2Kn0FCnA03f8PPpste99uNXU2tDSycRsM5a1wEHEdavBd%2Fxm2zRFUpRjbQ324GXcHqV7WVGE%2FIle7q6UpBOWNIIc5KLXxbzWO039IHHczyRtSjgIgZPH33LZz6bU1THcjLyGeSQA%2FZDBkTXT2nkynbXCAJM0OBcww7CMHHx6Ar3QD0A46ovFykpW%2FTOHtLUEfgDIVS9jwzGvLStnElXaa8m4sAk6QunOBVmbN%2FOzOh28NPCGBSOY8eru2CaqY57Z7xEIKoJslILFV'
        response = requests.get(url, params={'view': 'mRoster'}, cookies={'swid': swid, 'espn_s2': espn_s2}).json()
        
        # PLAYER SLOTS
        # response['teams'][5]['roster']['entries'][2]['playerPoolEntry']['player']['eligibleSlots']
        rosters = {}
        for team in response['teams']:
            teamID = team['id']
            rosters[teamID] = [player['playerPoolEntry']['player']['fullName'] for player in team['roster']['entries']]
        
        response = requests.get(url, params={'view': 'mSettings'}, cookies={'swid': swid, 'espn_s2': espn_s2}).json()
        # TODO: ADD AUTO SCORING
        for stat in response['settings']['scoringSettings']['scoringItems']:
           self.scoring[stat['statId']] = stat['points']
        print(self.scoring)

        response = requests.get(url, cookies={'swid': swid, 'espn_s2': espn_s2}).json()
        self.name = response['settings']['name']
        self.teams = response['teams']
        for team in self.teams:
            del team['owners']
            team['roster'] = rosters[team['id']]

categories = ("g", "mp", "fg", "fga", "fg_pct", "fg3", "fg3a", "fg3_pct", "ft", "fta", "ft_pct", "trb", "ast", "stl", "blk", "tov", "pts")
scoring = {"fg": 1, "fga": -1, "ft": 1, "fta": -1, "trb": 1.2, "ast": 1.5, "stl": 3, "blk": 3, "tov": -1, "pts": 1}
standardPos = ('PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', '', 'UTL', 'UTL', 'UTL')
seasonurl = 'https://www.basketball-reference.com/leagues/NBA_2020_totals.html'
leagueurl = "https://fantasy.espn.com/apis/v3/games/fba/seasons/2020/segments/0/leagues/17451714"

team = ["Terry Rozier", "Malcolm Brogdon", "LeBron James", "Danilo Gallinari", "Tristan Thompson", "Luka Dončić", "D'Angelo Russell", "Nikola Jokić", "De'Aaron Fox", "Jabari Parker", "Zion Williamson", "Shai Gilgeous-Alexander", "Aron Baynes"]
compare = ["D'Angelo Russell", "Danilo Gallinari"]
# printStats(averageStats(team))

special = {'Luka Doncic': "Luka Dončić", 'Nikola Jokic': "Nikola Jokić"}

fantasy = League(leagueurl)
print(fantasy.name)

# league = getTeams(fantasy)

# for team in league: # replace names with special characters
#     for i in range(len(team)):
#         if team[i] in special:
#             team[i] = special[team[i]]

# for key in fantasy['teams'][1]['roster']['entries']:
#     print(key)
# averages = averageStats(compare)
# printStats(averages)

# 1.0 0 PTS
# 3.0 1 BLK
# 3.0 2 STL
# 1.5 3 AST
#     4 ORB
#     5 DRB
# 1.2 6 REB
#     7 EJCT
#     8 FLGRNT
#     9 PF
#     10 TECHF
# -1.0 11 TOV
#      12 DQ
# 1.0 13 FGM
# -1.0 14 FGA
# 1.0 15 FTM
# -1.0 16 FTA
# 17 3PM
# 18 3PA
# 19 FG%
# 20 FT%
# 21 3P%
# 22 EFG%
# 23 FG MISSED
# 24 FT MISSED
# 25 3P MISSED
# 37 DBL DBL
# 38 TRPL DBL
# 39 QDRPL DBL
# 40 MIN
# 41 GS
# 42 GP
# 43 TM WINS

