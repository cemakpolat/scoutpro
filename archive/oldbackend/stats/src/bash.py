"""
@author: Cem Akpolat
@created by cemakpolat at 2021-09-06
"""

bashCommand = "docker-compose up"
import subprocess
process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
output, error = process.communicate()
print(output)
