import os
import requests
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()


class MC:
    # crafty controller init
    ccAccUname = os.getenv("CC_USERNAME")
    ccAccPass = os.getenv("CC_PASSWORD")
    ccToken = None  # to store token from crafty controller when started
    baseURL = os.getenv("BASE_CRAFTY_URL")
    verifySSL = False

    # Sets the Crafty Controller token
    def prepCraftyToken(self):
        global ccToken
        loginUrl = f"{self.baseURL}/auth/login"
        loginPayload = {
            "username": f"{self.ccAccUname}",
            "password": f"{self.ccAccPass}"
        }

        loginResp = requests.post(loginUrl, json=loginPayload, verify=self.verifySSL)
        loginResp.raise_for_status()

        ccToken = loginResp.json()["data"]["token"]
        print("Token:", ccToken)


    # web requests for pulling mc server
    # returns list of servers
    def getServers(self):
        global ccToken
        headers = {
            "Authorization": f"Bearer {ccToken}"
        }
        resp = requests.get(f"{self.baseURL}/servers/", headers=headers, verify=self.verifySSL)
        resp.raise_for_status()

        data = resp.json()["data"]  # list of servers
        return [(server["server_name"], server["server_id"])for server in data]


    # web requests for pulling mc server ID with provided name
    # returns the string server ID
    def getServerID(self, name):
        global ccToken
        headers = {
            "Authorization": f"Bearer {ccToken}"
        }
        resp = requests.get(f"{self.baseURL}/servers/", headers=headers, verify=self.verifySSL)
        resp.raise_for_status()

        data = resp.json()["data"]  # list of servers
        return [(server["server_name"], server["server_id"])for server in data]


    # whitelist a player on crafty controller server by player name and server ID
    # returns true if able to send command to server
    def whitelistPlayer(self, serverID, playerName):
        global ccToken
        url = f"{self.baseURL}/servers/{serverID}/stdin"
        headers = {
            "Authorization": f"Bearer {ccToken}"
        }

        resp = requests.post(url, headers=headers, data=f"/whitelist add {playerName}", verify=self.verifySSL)
        resp.raise_for_status()

        return resp.status_code == 200


    # get the status of a crafty controller server by name
    # response data includes server name, running status, description, and player count
    def getStatus(self, serverName):
        global ccToken
        url = f"{self.baseURL}/servers/"
        headers = {
            "Authorization": f"Bearer {ccToken}"
        }
        resp = requests.get(url, headers=headers, verify=self.verifySSL)
        resp.raise_for_status()

        data = resp.json()["data"]

        for server in data:
            worldName = server["server_name"]
            if serverName == worldName:
                serverID = server["server_id"]
                statsURL = f"{self.baseURL}/servers/{serverID}/stats"
                statsResp = requests.get(statsURL, headers=headers, verify=self.verifySSL)
                statsResp.raise_for_status()
                stats = statsResp.json()["data"]

                return [
                    serverName,  # name
                    stats["running"],  # running boolean
                    stats["desc"],  # description
                    stats["players"],  # players list/string
                ]

        return None


    # get the metrics of a crafty controller server by name
    # response data includes server name, cpu utilization, memory utilization, memory percentage
    def getMetrics(self, serverName):
        global ccToken
        url = f"{self.baseURL}/servers/"
        headers = {
            "Authorization": f"Bearer {ccToken}"
        }
        resp = requests.get(url, headers=headers, verify=self.verifySSL)
        resp.raise_for_status()

        data = resp.json()["data"]

        for server in data:
            worldName = server["server_name"]
            if serverName == worldName:
                serverID = server["server_id"]
                statsURL = f"{self.baseURL}/servers/{serverID}/stats"
                statsResp = requests.get(statsURL, headers=headers, verify=self.verifySSL)
                statsResp.raise_for_status()
                stats = statsResp.json()["data"]

                return [
                    serverName,
                    stats["cpu"],
                    stats["mem"],
                    stats["mem_percent"],
                ]

        return None