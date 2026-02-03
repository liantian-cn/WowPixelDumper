import time
import importlib
import requests




class RotateEngine:
    def __init__(self,profile="PriestDiscipline"):
        self.profile = profile
        self.session = requests.Session()
        # 动态按profile加载文件名为{profile}.py文件内的rotarion函数
        self.rotation = getattr(importlib.import_module(f"{profile}"), "rotation")

    def go(self):
        while True:
            self.rotation = getattr(importlib.import_module(f"{self.profile}"), "rotation")
            req = self.session.get("http://127.0.0.1:65131/api")
            data = req.json()

            result = self.rotation(data)
            print(result)
            time.sleep(1)
        
if __name__ == "__main__":

    handler = RotateEngine()

    handler.go()