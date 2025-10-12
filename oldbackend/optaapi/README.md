How to store the files in the database?

F1 - all matches given season and competition
F9 - single match 
F24 - single match, all vents
F40 - teams in the competition

## Data Parsing & Gathering

### 1.1 Data Parsing & Cleaning

- Define all required parsing functions, convert them to the classes and then store using MongoEngine classes
- 

### 1.2 Database Integration & Database API Implementation


### 1.3 Live Feed Data Interface Implementation

## 2. Feed APIs

Player API	
- F40	getPlayerData 	get all player data
- F24	calculateGamesPlayed	caclulate the number of games played by the player in a season
- F24	calculateMinutesPlayed	calculate the number of minutes played by the player in a season
- F1, F24	getPlayerStatistics (Total)	get all player statistics for the games the player played in a given season
- F1, F24	getPlayerStatistics (perGame)	get all player statistics for the games the player played in a given season per game
- F1, F24	getPlayerStatistics (per90)	get all player statistics for the games the player played in a given season per 90 minutes
- F24	getGoalkeeperStatistics	get goalkeeper related statistics for a given season
- F24	getPlayerPassEvents	Detailed analysis of pass events (pass distance, pass location etc.)
- F24	getPlayerShotEvents	Detailed analysis of shot events 
- F24	getTeamFormation	get team formation with formation & player changes
- F40,F24	comparePlayers(p1,p2)	create a similarity (distance) metric to compare two players in the same position
- F40,F24	rankLeagueplayers(p1,pN)	for a given set of data, rank all players in the league from best to worst
			
			
			
Game/Match API	F9	getGameData(season)	
Team API	F40	getTeamData(season)	
		getTeamStatistics(season)	
Official API		getOfficialData(official name)	


### 2.1 Designing an API concept covering live and stored data
### 2.2 Implementation of Player & Official APIs, Game & Team APIs, Event API

## 3. Data Analytic APIs | Knowledge Layer

### 3.1 Identifying Required Features & Libs
### 3.2 Integrating Data Analytic Libs 
### 3.3 Implementing Player, Team, Official and Match Functions/Algorithms using Data Analytic Libs

## 4. Applications & Visualization of Data

### 4.1 Designing and Implementing a concept for Data Visualization
### 4.2 Scout App
### 4.3 Player Performance App
### 4.4 Tactic Management App (Short-term & Long-term)

## 5 Simulation Environment

### 5.1 Designing & Implementing a Simulation Environment for Games, Players, etc

Python Agent Framework: PADE Framework - https://pade.readthedocs.io/en/latest/user/enviando-mensagens.html




Password: eagle

#### Flask 

FLASK_APP=hello.py flask run --host=0.0.0.0 --port 5555

#### MongoDB


MongoCompass can connect to the ip and port number and visualize the latest data in the database.
MongoDB default does not support for all network interfaces as flask. Therefore its configuration file has to be adapted[1].
[1]https://medium.com/founding-ithaka/setting-up-and-connecting-to-a-remote-mongodb-database-5df754a4da89

Default Apache HTTP Web Server is accessible via http://145.14.158.208/

Requirement Installations

1. Done, Add new sudo user https://linuxize.com/post/how-to-create-a-sudo-user-on-ubuntu/
2. Done, Install mongodb https://www.digitalocean.com/community/tutorials/how-to-install-mongodb-on-ubuntu-18-04
3. Done, Install firewall and make the mongoDB accessible https://linuxize.com/post/how-to-setup-a-firewall-with-ufw-on-ubuntu-18-04/
4. Done, Install git
5. Done, import the GitHub project code
6. Pending, low priority , gitlab server for the development environment: https://about.gitlab.com/install/#ubuntu
7. Pending, implementation of simple python code for fetching the database from the Opta and save in the processed data in the mongodb
8. Pending, demsifying Opta data model, extracting the correlation between the fetched xml/json data models
9. Flask + MongoDB Tutorial,  https://devinpractice.com/2019/03/25/flask-mongodb-tutorial/
   1. https://medium.com/@riken.mehta/full-stack-tutorial-flask-react-docker-ee316a46e876
   https://medium.com/@smirnov.am/running-flask-in-production-with-docker-1932c88f14d0
   2. https://github.com/codehandbook/PythonMongoAPI/blob/master/app.py
   3. https://github.com/Moesif/moesif-flask-mongo-example
      1. https://www.moesif.com/blog/technical/restful/Guide-to-Creating-RESTful-APIs-using-Python-Flask-and-MongoDB/#
10. Use This approach: Flask-mongorest-mongoengine
    1. https://github.com/closeio/flask-mongorest
11. Ongoing, http server implementation, flask uses python and a simple hello word: http://145.14.158.208:5000/ 
    1. How to use flask: http://flask.pocoo.org/docs/0.12/quickstart/
    2. Later this will be used: https://www.afternerd.com/blog/python-http-server/
12. Ongoing, create development environment for python3 https://www.digitalocean.com/community/tutorials/how-to-install-python-3-and-set-up-a-programming-environment-on-ubuntu-18-04-quickstart
13. Ongoing, implementation of mongodb interface: http://api.mongodb.com/python/current/tutorial.html
    1. Implement this link: https://www.bogotobogo.com/python/MongoDB_PyMongo/python_MongoDB_RESTAPI_with_Flask.php
    2. Python mongo-flask https://flask-pymongo.readthedocs.io/en/latest/
14. Pending, installation of pyenv for python package manger that controls python2-3, detailed exp: https://realpython.com/intro-to-pyenv/
    1. "One final aspect of pyenv that I enjoy is the ability to set a default environment for a given directory. This causes the desired environment to be automatically activated when I enter a directory. I find this a lot easier than trying to remember which environment I want to use every time I work on a project."[https://towardsdatascience.com/which-python-package-manager-should-you-use-d0fd0789a250]
15. Pending, moving from the basic kanban to automated kanban in GitHub https://medium.com/the-andela-way/how-to-build-a-power-up-for-your-github-project-board-for-project-management-344d5b380a68
16. Pending, setup a python environment for ML: https://towardsdatascience.com/setup-an-environment-for-machine-learning-and-deep-learning-with-anaconda-in-windows-5d7134a3db10
17. Pending, python machine learning installation and tools: https://www.accelebrate.com/library/tutorials/machine-learning-part1
18. imrankhan17/Parsing-Opta-files
19. Parsing Opta F24 Files: An Introduction to XML in Python | FC Python





Python libraries to be used:

asynch - https://mail.google.com/mail/u/0/#inbox/QgrcJHsBpWBSWzZGvxlbzZZmJKmqrjDscMq

request - https://stackoverflow.com/questions/6386308/http-requests-and-json-parsing-in-python

python-json:

- http://www.compjour.org/tutorials/intro-to-python-requests-and-json/
- https://realpython.com/python-json/
- https://www.makeuseof.com/tag/json-python-parsing-simple-guide/
- https://2.python-requests.org//en/latest/user/quickstart/#json-response-content
- 


Blueprint: https://realpython.com/flask-blueprint/


F1 REST 
 
F1 delivers only the matches with less information,  
 
- GET /competition/season/matches 
  - refined match data that involves 
    - match general info 
      - did 
    - matchinfo,  GET /competition/season/match/id/info 
          { 
            matchday:"", 
            matchtype:"",  
            matchwinner:"", 
            period:,  
            venue_id:"",  
            tz:"",  
            date:"" 
          } 
       
    - matchofficials, `GET/competition/season/match/id/officials 
          [ 
            firstname:"", 
            lastname:"", 
            type:"", 
            uId:"o44476"  
          ] 
    - matchstats, GET  /competition/season/match/id/stats 
          { 
            venue:"", 
            city:"", 
            ... 
          } 
       
    - teamdata, GET /competition/season/match/id/teamdata 
      - For each team -> return team data 
        - return  
              { 
                halfscore:"",  
                score:"",  
                side:"",  
                teamref {t_208} 
                goals: { 
                  period:"",  
                  playerRef:"", 
                  type:"" 
                } 
               
           
- GET /competion/season/teams 
  - it returns only team names and team id (t_208) 
        [ 
        	{name:"",ref:""}, 
        	{name:"",ref:""}, 
        	... 
        ] 
 
F9 REST 
 
F9 returns the result of single match. 
 
- GET /competition/season/match/matchid 
  - general info 
        {type:"",uID:""} 
     
  - matchdata, GET competition/season/match/matchid/matchdata 
    - matchinfo 
          { 
            data:"", 
            additionaInfo:"", 
            matchtype:"", 
            period:"", 
            timestamp:"" 
          } 
       
    - matchofficial 
          [ 
            { 
              type:main, 
              first:"cuneyt" 
              last:"cakir", 
              uID:"" 
            },{...} 
          ]	 
       
    - assistantofficials 
          [ 
            { 
              firstname:"", 
              secondname:"", 
              type:"", 
              uID:"043856" 
            }, 
            {...} 
          ] 
       
    - stats 
          [ 
            { 
              type:"match_time", 
              value:"71" 
            }, 
          ] 
       
    - teamdata 
      - booking 
            [ 
              { 
                card:"yellow", 
                cardtype:"yellow", 
                eventId:"", 
                eventnumber:"", 
                min:"", 
                period:"", 
                playerRef:"", 
                reason:"foul", 
                sec:"", 
                time:"", 
                timestamp:"", 
                uID:"b2136-1" 
              },{ 
                ... 
              } 
            ] 
         
      - goal 
            [ 
              { 
                assist:{ 
                  playerref:"p84.." 
                }, 
                eventID:"", 
                eventNumber:"", 
                min:"", 
                period:"", 
                sec:"", 
                time:"", 
                timestamp:"", 
                type:"Goal", 
                uID:"", 
              },{ 
                ... 
              } 
            ] 
         
      - playerlineup 
            [ 
              { 
                playerref:"", 
                position:"goalkeeper", 
                shirtnumber:13, 
                status:"start", 
                stats:[ 
                  { 
                    type:"diving_save", 
                    value:1 
                  },{ 
                    type:"leftside_pass", 
                    value:4 
                  },{ 
                    type:"accurate_pass", 
                    value:10 
                  }, 
                  ... 
                ] 
              } 
            ] 
         
      - stats 
            [ 
              { 
               type:"total flickon", 
               value:4, 
               fh:4, 
               sh:0 
              }, 
               { 
                type:"leftside_pass", 
               	value:110, 
            	  fh:56, 
            	  sh:54 
              }, 
              ... 
            ] 
         
      - substitiution: 
            { 
              eventId:2323, 
              eventNumber:1427, 
              min:"41", 
              period:"1", 
              reason:"tactical", 
              sec:21, 
              suboff:"p8489", 
              subon:"p166070", 
              substitutePosition:2, 
              time:42, 
              timestamp:"" 
              uId:"s2136-1" 
            } 
         
      - general info:  
            { 
              score:"2", 
              side:"home", 
              teamref:"t2136" 
            } 
         
     
  - team,  GET competition/season/match/matchid/teams 
        { 
          name:"", 
          uId:"", 
          country:"", 
          kit:{ 
            id:"", 
            colour1:"", 
            colour2:"", 
            type:"home" 
          }, 
          players:[ 
            { 
              first:"", 
              last:"", 
              position:"", 
              uID:"" 
            },{..} 
          ], 
          teamofficial:{ 
            first:"", 
            last:"", 
            type:"manager", 
            uID:"" 
          } 
        } 
     
  - competition,  GET competition/season/match/matchid/competition 
        { 
        country:"", 
        name:"", 
        uID:"", 
        stats:[ 
          season_id:"", 
          season_name:"", 
          symid:"", 
          matchday:"" 
        ] 
        } 
     
  - venue, GET competition/season/match/matchid/venue 
      { 
        country:"", 
        name:"", 
        uID:"" 
      } 
       
 
 
 
F24 REST  
 
    { 
      id:"", 
      away_score:"", 
      away teamid:"", 
      away teamname:"", 
      competition_id:"", 
      competition_name:"", 
      game_date:"", 
      home_score:"", 
      home teamid:"", 
      home teamname:"", 
      matchday:"", 
      period 1start:"", 
      period 2start:"", 
      season_id:"", 
      season_name:"", 
      events:[ 
        {  
          id:"", 
          event_id:"", 
          type_id:"", 
          period_id:"", 
          min:"", 
          sec:"", 
          team_id:"", 
          outcome::"", 
          x:"", 
          y:"", 
          timestamp:"", 
          lastmodified:"?" 
          version:"", 
          q:[ 
            id:"", 
            qualfier_id:"", 
            value:"" 
          ] 
        } 
      ] 
    } 
 
 
 
F40 REST 
 
- general info 
      { 
        type:"", 
      	competiotion_code:"", 
      	competition_id:"", 
      	competition_name:"", 
      	season_id:"", 
      	season_name:"", 
      } 
- teams ,ok
      [ 
        { 
        name:"", 
        players:[ 
        { 
        name:"", 
        position:"", 
        uID:"", 
        stats:[ 
        {type:"",value:""},{...} 
        ] 
        } 
        ], 
        syimd:"ALN", 
        stadium:{ 
          capacity:"", 
          name:"", 
          uID:"", 
        } 
        kits:[ 
        id:"", 
        colour1:"", 
        colour2:"", 
        type:"home" 
        ], 
        teamofficials:[ 
          { 
          first:"", 
          last:"", 
          birthdate:"", 
          joinDate:"", 
          type:"", 
          country:"", 
          uID:"", 
          },{} 
        ], 
        country:"", 
        country_id:"", 
        country_iso:"", 
        region_id:"", 
        region_name:"", 
        short ckubname:"", 
        uID:"", 
        } 
      ] 
   
- playerChanges  
      [ 
        { 
          name:"", 
          uID:"" 
          players:[ 
          { 
            name:"", 
            position:"", 
            stats:[ 
              type:"", 
              value:"" 
            ], 
            loan:"", 
            uID:"p19.." 
          }   
          ], 
          teamofficials:[ 
            { 
              personname:{ 
                first:"", 
                last:"", 
                joinDate:"", 
                leaveDate:"", 
                birhtDate:"", 
                type:"", 
                country:"", 
                uID:"", 
              } 
            } 
          ] 
        } 
      ] 
  

Doruk questions
1. line 266 270,  playerID is the event player ID

