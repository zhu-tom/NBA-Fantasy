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
                if type(player[key]) != str:
                    print(f"{player[key]:<8.3f}", end="")
                else:
                    print(f"{player[key]:<8}", end="")
        print()

def getTeams(json):
    return [[player['playerPoolEntry']['player']['fullName'] for player in team['roster']['entries']] for team in fantasy['teams']]

statKey = {0: 'pts', 1: 'blk', 2: 'stl', 3: 'ast', 4: 'orb', 5: 'drb', 6: 'trb', 11: 'tov', 13: 'fg', 14: 'fga', 15: 'ft', 16: 'fta', 17: 'fg3', 18: 'fg3a', 19: 'fg_pct', 20: 'ft_pct', 21: 'fg3_pct', 22: 'efg_pct', 23: 'fgmi', 24: 'ftmi', 25: 'fg3mi'}
posKey = ('PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'SG/SF', 'G/F', "PF/C", "F/C", 'UTL', 'BE', 'IR', 'EXTRA')

class Team:
    teamID = ""
    roster = []
    teamName = ""
    playoffSeed = 0
    totals = {}

    def __init__(self, League, teamInfo):
        self.abbrev = teamInfo['abbrev']
        self.teamID = teamInfo['id']
        self.teamName = teamInfo['location'] + teamInfo['nickname']
        self.division = League.divisions[teamInfo['divisionId']]
        self.playoffSeed = teamInfo['playoffSeed']
        self.record = teamInfo['record']
        self.transactions = teamInfo['transactionCounter']
        self.waiverRank = teamInfo['waiverRank']
        for key in teamInfo['valuesByStat']:
            self.totals[statKey[int(key)]] = teamInfo['valuesByStat'][key]
        self.League = League

    def setRoster(self, json):
        for playerInfo in json:
            self.roster.append(Player(self.League, self, playerInfo))

class Player:
    name = ""
    totals = {}
    averages = {}
    gameLog = {}
    eligibleSlots = []
    team = Team

    def __init__(self, League, Team, playerInfo):
        self.id = playerInfo['playerId']
        self.acquisition = {'day': playerInfo['acquisitionDate'], 'type': playerInfo['acquisitionType']}
        self.slotID = playerInfo['lineupSlotId']
        self.droppable = playerInfo['playerPoolEntry']['player']['droppable']
        print(League.rosterBuild)
        # TODO ADD ELIGIBLE POSITIONS BASED ON LEAGUE SETTINGS
        for position in playerInfo['playerPoolEntry']['player']['eligibleSlots']:
            print(posKey[position], end=" ")
            self.eligibleSlots.append(posKey[position])
        print()



class League:
    name = ""
    teams = []
    leagueType = ""
    rosterBuild = {}
    divisions = ()

    def __init__(self, leagueID, season):
        swid = '{2C5C7745-8766-42EC-A3F1-7A0B7B109444}'
        espn_s2 = 'AECmhjRVqnP2Kn0FCnA03f8PPpste99uNXU2tDSycRsM5a1wEHEdavBd%2Fxm2zRFUpRjbQ324GXcHqV7WVGE%2FIle7q6UpBOWNIIc5KLXxbzWO039IHHczyRtSjgIgZPH33LZz6bU1THcjLyGeSQA%2FZDBkTXT2nkynbXCAJM0OBcww7CMHHx6Ar3QD0A46ovFykpW%2FTOHtLUEfgDIVS9jwzGvLStnElXaa8m4sAk6QunOBVmbN%2FOzOh28NPCGBSOY8eru2CaqY57Z7xEIKoJslILFV'
        url = "https://fantasy.espn.com/apis/v3/games/fba/seasons/"+ str(season) + "/segments/0/leagues/" + str(leagueID)
        special = {'Luka Doncic': "Luka Dončić", 'Nikola Jokic': "Nikola Jokić", 'Bojan Bogdanovic': 'Bojan Bogdanović', 'Tomas Satoransky': 'Tomáš Satoranský'}
        
        # LEAGUE INFO
        response = requests.get(url, params={'view': 'mSettings'}, cookies={'swid': swid, 'espn_s2': espn_s2}).json()
        self.name = response['settings']['name']
        # TODO: ADD AUTO SCORING
        lineupSettings = response['settings']['rosterSettings']['lineupSlotCounts']
        for key in lineupSettings:
            if lineupSettings[key] > 0:
                self.rosterBuild[posKey[int(key)]] = lineupSettings[key]
        del lineupSettings

        self.divisions = (response['settings']['scheduleSettings']['divisions'][0]['name'], response['settings']['scheduleSettings']['divisions'][1]['name'])
        
        self.leagueType = response['settings']['scoringSettings']['scoringType']
        if self.leagueType == 'H2H_POINTS' or self.leagueType == 'TOTAL_SEASON_POINTS':
            self.scoring = {}
            for stat in response['settings']['scoringSettings']['scoringItems']:
                self.scoring[statKey[stat['statId']]] = stat['points']

        # TEAMS
        response = requests.get(url, params={'view': 'mTeam'}, cookies={'swid': swid, 'espn_s2': espn_s2}).json()
        for teamInfo in response['teams']:
            self.teams.append(Team(self, teamInfo))

        response = requests.get(url, params={'view': 'mMatchup'}, cookies={'swid': swid, 'espn_s2': espn_s2}).json()
        
        # PLAYER SLOTS
        # response['teams'][5]['roster']['entries'][2]['playerPoolEntry']['player']['eligibleSlots']
        for team in response['teams']:
            for leagueTeam in self.teams:
                if leagueTeam.teamID == team['id']:
                    leagueTeam.setRoster(team['roster']['entries'])
        
        

categories = ("g", "mp", "fg", "fga", "fg_pct", "fg3", "fg3a", "fg3_pct", "ft", "fta", "ft_pct", "trb", "ast", "stl", "blk", "tov", "pts")
scoring = {"fg": 1, "fga": -1, "ft": 1, "fta": -1, "trb": 1.2, "ast": 1.5, "stl": 3, "blk": 3, "tov": -1, "pts": 1}
seasonurl = 'https://www.basketball-reference.com/leagues/NBA_2020_totals.html'
leagueID = '17451714'
year = '2020'

team = ["Terry Rozier", "Malcolm Brogdon", "LeBron James", "Danilo Gallinari", "Tristan Thompson", "Luka Dončić", "D'Angelo Russell", "Nikola Jokić", "De'Aaron Fox", "Jabari Parker", "Zion Williamson", "Shai Gilgeous-Alexander", "Aron Baynes"]
compare = ["D'Angelo Russell", "Danilo Gallinari"]
# printStats(averageStats(team))


fantasy = League(leagueID, year)
#printStats(gameLog('Danilo Gallinari'))
# printStats(averageStats(fantasy.teams[5]['roster']))

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

