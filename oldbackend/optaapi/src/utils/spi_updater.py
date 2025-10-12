import os
import requests
import pathlib
import time
from timeloop import Timeloop
from datetime import timedelta


class SPIUpdater:
    def __init__(self, tl, interval=None):
        self.tl = tl
        self.time_interval = (
            5  # every five day this code will be executed to download the latest spis
        )
        if interval is not None:
            self.time_interval = interval

    def getFile(self, url):
        URL = url
        PARAMS = {}
        data = requests.get(url=URL, params=PARAMS)
        return data

    def save(self, fileName, data):
        # dir_path = os.path.dirname(os.path.realpath(__file__))
        # print(dir_path)
        parentPath = pathlib.Path(os.getcwd()).parent
        print(pathlib.Path(os.getcwd()).parent)
        pathlib.Path(str(parentPath) + "/csv/").mkdir(parents=True, exist_ok=True)

        # Check folder does exist, if not then create it and add the following files

        with open(str(parentPath) + "/csv/" + fileName + ".csv", "wb") as f:
            f.write(data.content)

    def downloadSPIFiles(self):
        print("Beginning file download with requests")

        self.save(
            "spi_global_rankings",
            self.getFile(
                "https://projects.fivethirtyeight.com/soccer-api/club/spi_global_rankings.csv"
            ),
        )
        self.save(
            "spi_matches",
            self.getFile(
                "https://projects.fivethirtyeight.com/soccer-api/club/spi_matches.csv"
            ),
        )
        self.save(
            "spi_global_rankings_intl",
            self.getFile(
                "https://projects.fivethirtyeight.com/soccer-api/club/spi_global_rankings_intl.csv"
            ),
        )

    def startTimeLoop(self):
        # Every 5 day the following function will be called to update
        # a separate thread is started for timeloop. When the program is killed, this stops as well.
        @self.tl.job(
            interval=timedelta(seconds=self.time_interval)
        )  # seconds, minutes,
        def sample_job_every_given_day():
            print("3 days job current time : {}".format(time.ctime()))
            self.downloadSPIFiles()

        self.tl.start(
            block=True
        )  # This stops the executed separate thread, there is no need to stop the thread expilicitly.


# if __name__ == "__main__":
#     spi = SPIUpdater(Timeloop())
#     spi.startTimeLoop()
