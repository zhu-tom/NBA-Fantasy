from bs4 import BeautifulSoup
import requests
import unicodedata

statKey = {0: 'pts', 1: 'blk', 2: 'stl', 3: 'ast', 4: 'orb', 5: 'drb', 6: 'trb', 11: 'tov', 13: 'fg', 14: 'fga', 15: 'ft', 16: 'fta', 17: 'fg3', 18: 'fg3a', 19: 'fg_pct', 20: 'ft_pct', 21: 'fg3_pct', 22: 'efg_pct', 23: 'fgmi', 24: 'ftmi', 25: 'fg3mi'}
posKey = ('PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'SG/SF', 'G/F', "PF/C", "F/C", 'UTL', 'BE', 'IR', 'EXTRA')
proTeams = {1:'ATL', 2:'BOS', 3:'NOP', 4:'CHI', 5:'CLE', 6:'DAL', 7:'DEN', 8:'DET', 9:'GSW', 10:'HOU', 11:'IND', 12:'LAC', 13:'LAL', 14:'MIA', 15:'MIL', 16:'MIN', 17:'BKN', 18:'NYK', 19:'ORL', 20:'PHI', 21:'PHX', 22:'POR', 23:'SAC', 24:'SAS', 25:'OKC', 26:'UTA', 27:'WAS', 28:'TOR', 29:'MEM', 30:'CHA'}
special = {'Luka Doncic': "Luka Dončić", 'Nikola Jokic': "Nikola Jokić", 'Bojan Bogdanovic': 'Bojan Bogdanović',
    'Tomas Satoransky': 'Tomáš Satoranský', 'Marvin Bagley III': 'Marvin Bagley', "Wendell Carter Jr.": "Wendell Carter",
         "Jonas Valanciunas": "Jonas Valančiūnas", "Kristaps Porzingis": "Kristaps Porziņģis", 'Bogdan Bogdanovic': 'Bogdan Bogdanović', 
         "Goran Dragic": "Goran Dragić", "Nikola Vucevic": "Nikola Vučević", "Kelly Oubre Jr.":"Kelly Oubre", "Dennis Schroder": "Dennis Schröder",
         "Marcus Morris Sr.": "Marcus Morris"}
statHead = {'averages': ("name", 'g', "mp", "fg", "fga", "fg_pct", "fg3", "fg3a", "fg3_pct", "ft", "fta", "ft_pct", "trb", "ast", "stl", "blk", "tov", "pts", 'fpts'), 
            'gamelog': ('date', "mp", "fg", "fga", "fg_pct", "fg3", "fg3a", "fg3_pct", "ft", "fta", "ft_pct", "trb", "ast", "stl", "blk", "tov", "pts")}
categories = ("g", "mp", "fg", "fga", "fg_pct", "fg3", "fg3a", "fg3_pct", "ft", "fta", "ft_pct", "trb", "ast", "stl", "blk", "tov", "pts")

def getSoup(url: str) -> BeautifulSoup:
    response = requests.get(url)
    html = BeautifulSoup(response.text, 'html.parser')
    return html

class League:
    swid = '{2C5C7745-8766-42EC-A3F1-7A0B7B109444}'
    espn_s2 = 'AECmhjRVqnP2Kn0FCnA03f8PPpste99uNXU2tDSycRsM5a1wEHEdavBd%2Fxm2zRFUpRjbQ324GXcHqV7WVGE%2FIle7q6UpBOWNIIc5KLXxbzWO039IHHczyRtSjgIgZPH33LZz6bU1THcjLyGeSQA%2FZDBkTXT2nkynbXCAJM0OBcww7CMHHx6Ar3QD0A46ovFykpW%2FTOHtLUEfgDIVS9jwzGvLStnElXaa8m4sAk6QunOBVmbN%2FOzOh28NPCGBSOY8eru2CaqY57Z7xEIKoJslILFV'
        
    def __init__(self, leagueID, season):
        swid = '{2C5C7745-8766-42EC-A3F1-7A0B7B109444}'
        espn_s2 = 'AECmhjRVqnP2Kn0FCnA03f8PPpste99uNXU2tDSycRsM5a1wEHEdavBd%2Fxm2zRFUpRjbQ324GXcHqV7WVGE%2FIle7q6UpBOWNIIc5KLXxbzWO039IHHczyRtSjgIgZPH33LZz6bU1THcjLyGeSQA%2FZDBkTXT2nkynbXCAJM0OBcww7CMHHx6Ar3QD0A46ovFykpW%2FTOHtLUEfgDIVS9jwzGvLStnElXaa8m4sAk6QunOBVmbN%2FOzOh28NPCGBSOY8eru2CaqY57Z7xEIKoJslILFV'
        url = "https://fantasy.espn.com/apis/v3/games/fba/seasons/"+ str(season) + "/segments/0/leagues/" + str(leagueID)
        
        # LEAGUE INFO
        response = requests.get(url, params={'view': 'mSettings'}, cookies={'swid': self.swid, 'espn_s2': self.espn_s2}).json()
        try:
            settings = response['settings']
        except KeyError:
            print("Error: League is private. Please set cookies swid and espn_s2")
            return None

        self.name = response['settings']['name']
        
        self.rosterBuild = {}
        lineupSettings = response['settings']['rosterSettings']['lineupSlotCounts']
        for key in lineupSettings:
            if lineupSettings[key] > 0:
                self.rosterBuild[posKey[int(key)]] = lineupSettings[key]
        del lineupSettings

        self.divisions = [div['name'] for div in response['settings']['scheduleSettings']['divisions']]
        
        self.leagueType = response['settings']['scoringSettings']['scoringType']
        if self.leagueType == 'H2H_POINTS' or self.leagueType == 'TOTAL_SEASON_POINTS':
            self.scoring = {}
            for stat in response['settings']['scoringSettings']['scoringItems']:
                self.scoring[statKey[stat['statId']]] = stat['points']

        self.rosterLocktime = response['settings']['rosterSettings']['rosterLocktimeType']

        # TEAMS
        response = requests.get(url, params={'view': 'mTeam'}, cookies={'swid': swid, 'espn_s2': espn_s2}).json()
        self.teams = [Team(self, teamInfo) for teamInfo in response['teams']]

        response = requests.get(url, params={'view': 'mRoster'}, cookies={'swid': swid, 'espn_s2': espn_s2}).json()
        for team in response['teams']:
            for leagueTeam in self.teams:
                if leagueTeam.teamID == team['id']:
                    leagueTeam.setRoster(team['roster']['entries'])
        
        # TODO
        # FREE AGENTS
        response = requests.get(url, params={'view': 'kona_player_info'}, cookies={'swid': swid, 'espn_s2': espn_s2}).json()

        
        # BBALL REF SEASON TOTALS
        seasonurl = f'https://www.basketball-reference.com/leagues/NBA_{season}_totals.html'
        self.totalsHTML = getSoup(seasonurl)

    def printStats(self, name, stat='averages', last=0):
        if stat=='averages' and last != 0:
            print("Error: try stat = 'gamelog'")
            return None
        
        if name in special:
            name = special[name]

        for key in statHead[stat]: # headers
            if key == 'name':
                print(f"{key:24}", end="")
            elif key == 'date':
                print(f"{key:15}", end="")
            else:
                print(f"{key:<8}", end="")
        print()
            
        for team in self.teams:
            for player in team.roster:
                if player.name == name:
                    player.printStats(stat=stat, last=last)

class Team:

    def __init__(self, league: League, teamInfo: dict) -> None:
        self.abbrev = teamInfo['abbrev']
        self.teamID = teamInfo['id']
        self.teamName = teamInfo['location'] + " " + teamInfo['nickname']
        self.division = league.divisions[teamInfo['divisionId']]
        self.playoffSeed = teamInfo['playoffSeed']
        self.record = teamInfo['record']
        self.transactions = teamInfo['transactionCounter']
        self.waiverRank = teamInfo['waiverRank']
        self.totals = {}
        for key in teamInfo['valuesByStat']:
            self.totals[statKey[int(key)]] = teamInfo['valuesByStat'][key]
        self.league = league

    def setRoster(self, json: dict) -> None:
        self.roster = []
        for playerInfo in json:
            member = Player(playerInfo['playerPoolEntry']['player']['fullName'], self.league)
            member.setUp(self.league, self, playerInfo)
            self.roster.append(member)
    
    def printAverages(self) -> None:
        for player in self.roster:
            player.getAverages()

        print(f"{self.teamName} ({self.abbrev}) {self.record['overall']['wins']}-{self.record['overall']['losses']}")

        for key in statHead['averages']:
            if key == 'name':
                print(f"{key:24}", end="")
            else:
                print(f"{key:<8}", end="")
        print()

        for player in self.roster:
            for key in player.averages:
                if key == 'name':
                    print(f"{player.averages[key]:24}", end="")
                else:
                    if type(player.averages[key]) != str:
                        print(f"{player.averages[key]:<8.3f}", end="")
                    else:
                        print(f"{player.averages[key]:<8}", end="")
            print()
                

class Player:

    def __init__(self, name: str, league: League) -> None:
        self.name = name
        if self.name in special:
            self.name = special[self.name]
        self.league = league
        
    def setUp(self, league: League, team: Team, playerInfo) -> None:
        self.id = playerInfo['playerId']
        self.acquisition = {'day': playerInfo['acquisitionDate'], 'type': playerInfo['acquisitionType']}
        self.currentSlot = posKey[playerInfo['lineupSlotId']]
        self.droppable = playerInfo['playerPoolEntry']['player']['droppable']
        self.eligibleSlots = [posKey[position] for position in playerInfo['playerPoolEntry']['player']['eligibleSlots'] if posKey[position] in league.rosterBuild.keys()]
        self.ownership = playerInfo['playerPoolEntry']['player']['ownership']
        self.nbaTeam = proTeams[playerInfo['playerPoolEntry']['player']['proTeamId']]
        self.injured = playerInfo['playerPoolEntry']['player']['injured']
        self.injuryStatus = playerInfo['playerPoolEntry']['player']['injuryStatus']
        self.ratingsByPeriod = playerInfo['playerPoolEntry']['ratings']
        self.rosterLocked = playerInfo['playerPoolEntry']['rosterLocked']
        self.tradeLocked = playerInfo['playerPoolEntry']['tradeLocked']
        self.lineupLocked = playerInfo['playerPoolEntry']['lineupLocked']
        self.keeperValue = playerInfo['playerPoolEntry']['keeperValue']
        self.keeperValueFuture = playerInfo['playerPoolEntry']['keeperValueFuture']
        self.leagueTeam = team


    def getTotals(self) -> None:
        scoring = self.league.scoring

        html = self.league.totalsHTML

        rows = html.find('tbody').findAll('tr', {'class': 'full_table'})

        self.totals = {} # initiate

        lname = self.name.split(" ")[1].lower()
        lname = u"".join([c for c in unicodedata.normalize('NFKD', lname) if not unicodedata.combining(c)])

        while len(rows) != 0:
            mid = len(rows) // 2
            name = rows[mid].find('td').find('a').text
            currlname = name.split(" ")[1].lower()
            currlname = u"".join([c for c in unicodedata.normalize('NFKD', currlname) if not unicodedata.combining(c)])
            if currlname == lname:
                for row in rows:
                    if row.find('td').find('a').text == self.name:
                        fpts = 0
                        for cat in categories:
                            val = row.find('td', {'data-stat': cat}).text
                            if val == "":
                                self.totals[cat] = 0
                            else:
                                self.totals[cat] = float(val) # insert stats under category
                            
                            if cat in self.league.scoring.keys(): # if category is scored
                                fpts += self.league.scoring[cat] * self.totals[cat] # add to total
                        self.totals['fpts'] = fpts
                        break
                break
            elif currlname < lname:
                rows = rows[mid+1:]
            else:
                rows = rows[:mid]

    def getAverages(self) -> None:
        doNotAvg = ('g', 'fg_pct', 'fg3_pct', 'ft_pct')

        self.getTotals()
        self.averages = {'name': self.name}
        for key in self.totals:
            self.averages[key] = self.totals[key]
            if key not in doNotAvg:
                self.averages[key] /= self.totals['g']

    def getGameLog(self, last: int=0) -> None:

        # Find href to player page from league totals page
        html = self.league.totalsHTML

        rows = html.find('tbody').findAll('tr', {'class': 'full_table'})

        lname = self.name.split(" ")[1].lower()
        lname = u"".join([c for c in unicodedata.normalize('NFKD', lname) if not unicodedata.combining(c)])

        nameFound = False
        while len(rows) != 0:
            mid = len(rows) // 2
            name = rows[mid].find('td').find('a').text
            currlname = name.split(" ")[1].lower()
            currlname = u"".join([c for c in unicodedata.normalize('NFKD', currlname) if not unicodedata.combining(c)])
        
            if currlname == lname:
                for row in rows:
                    if row.find('td').find('a').text == self.name:
                        nameLink = row.find('td', {'data-stat': 'player'}).find('a')
                        playerLink = nameLink['href'].replace('.html', "")
                        nameFound = True
                        break
                break
            elif currlname < lname:
                rows = rows[mid+1:]
            else:
                rows = rows[:mid]
        
        if not nameFound:
            print("Error: Name not found")
            return None

        # Use href to find game log page
        gamesPage = f"https://www.basketball-reference.com{playerLink}/gamelog/2020"

        html = getSoup(gamesPage)

        rows = html.find('tbody').findAll('tr')

        # add to games to game log
        avg = {'date': 'Average'}
        for cat in categories[1:]:
            avg[cat] = 0 
        avg['fpts'] = 0
        gp = 0

        self.gameLog = []
        for row in rows[-last:]:
            date = row.find('td', {'data-stat': 'date_game'}).text
            game = {'date': date}
            
            fpts = 0
            played = True
            for cat in categories[1:]:
                cell = row.find('td', {'data-stat': cat})
                if cell == None: # player is out, has no stats
                    played = False
                    game['mp'] = row.find('td', {'data-stat': 'reason'}).text
                    break # move to next game
                else: 
                    game[cat] = cell.text

                if game[cat] != "" and cat != 'mp':
                    game[cat] = float(game[cat]) # cast all values to float if possible
                    avg[cat] += game[cat]
                elif cat != 'mp':
                    game[cat] = 0
                else:
                    minutes = game[cat].split(":")
                    avg[cat] += int(minutes[0])+(float(minutes[1])/60)

                if cat in self.league.scoring: # if category is scored
                    fpts += self.league.scoring[cat] * game[cat] # add to total

            if played == True:
                game['fpts'] = fpts
                avg['fpts'] += game['fpts']
                gp += 1

            self.gameLog.append(game)

        for key in avg:
            if key != 'date':
                avg[key] /= gp
        
        self.gameLog.append(avg)
        
    
    def printStats(self, stat: str='averages', last: int=0):
        headers = statHead[stat]

        if stat == 'averages':
            self.getAverages()
            stats = [self.averages]
        elif stat == 'gamelog':
            self.getGameLog(last=last)
            stats = self.gameLog[:]
            avg = {'date': "Average"}
            # for key in self.averages:
            #     if key in self.gameLog[0]:
            #         avg[key] = self.averages[key]
            # stats.append(avg)
        else:
            print("Error: Not valid stat group")
            return None

        # for key in headers: # arbitrary player stat categories
        #     if key == 'name':
        #         print(f"{key:24}", end="")
        #     elif key == 'date':
        #         print(f"{key:15}", end="")
        #     else:
        #         print(f"{key:<8}", end="")
        # print()

        for player in stats:
            for key in player.keys():
                if key == 'name':
                    print(f"{player[key]:24}", end="")
                elif key == 'date':
                    print(f"{player[key]:15}", end="")
                else:
                    if type(player[key]) != str:
                        print(f"{player[key]:<8.3f}", end="")
                    else:
                        print(f"{player[key]:<8}", end="")
            print()
        
leagueID = '17451714'
year = '2020'

compare = ["D'Angelo Russell", "Danilo Gallinari"]

myLeague = League(leagueID, year)
for team in myLeague.teams:
    team.printAverages()
#player = Player('Luka Doncic', league=myLeague).printStats(stat='gamelog', last=0)
# myLeague.printStats('Khris Middleton', stat='gamelog')
# myLeague.printStats('Lauri Markkanen', stat='gamelog')

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