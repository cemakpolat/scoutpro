# Data Analytics


## MongoDB connection
```
from pymongo import MongoClient
from pprint import pprint

client = MongoClient('mongodb://localhost:27017/')

with client:
   
    db = client.testdb
    print(db.collection_names())

    status = db.command("dbstats")
    pprint(status)
```
resource: https://zetcode.com/python/pymongo/

## Google Cloud Tools
https://bluemedora.com/mongodb-on-google-cloud-how-to-set-it-up-and-keep-it-healthy/

