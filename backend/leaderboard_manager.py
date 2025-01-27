import pickle
import time

import numpy as np

from common import Score, encode

class LeaderboardManager:
    def __init__(self):
        self.threat_leaderboard: list[Score]
        self.nice_leaderboard: list[Score]
        self.init_leaderboard()
    
    def init_leaderboard(self):
        try:
            with open('./threat_leaderboard.pkl', 'rb') as f:
                self.threat_leaderboard = pickle.load(f)
        except FileNotFoundError:
                self.threat_leaderboard: list[Score] = []

        try:
            with open('./nice_leaderboard.pkl', 'rb') as f:
                self.nice_leaderboard = pickle.load(f)
        except FileNotFoundError:
                self.nice_leaderboard: list[Score] = []

    def save_leaderboard(self):
        with open('./threat_leaderboard.pkl', 'wb') as f:
            pickle.dump(self.threat_leaderboard, f)
        with open('./nice_leaderboard.pkl', 'wb') as f:
            pickle.dump(self.nice_leaderboard, f)
    
    def new_score(self, image: np.ndarray, score: float, last_debounce: float):
        threat_eligible = (len(self.threat_leaderboard) < 10 or score > self.threat_leaderboard[-1].score)
        nice_eligible = (len(self.nice_leaderboard) < 10 or score < self.nice_leaderboard[-1].score)

        if threat_eligible or nice_eligible:
            enc_image: str = "data:image/jpeg;base64," + encode(image)
            identifier: str = f"{time.time()}_{hash(enc_image)}"
            
            try:
                new_score = Score(id=identifier, image=enc_image, name="", score=score)
            except Exception as e:
                print(f"Error creating new score: {e}")
                return last_debounce
            
            if threat_eligible:
                self.threat_leaderboard.append(new_score)
                self.threat_leaderboard.sort(key=lambda x: x.score, reverse=True)
                self.threat_leaderboard = self.threat_leaderboard[:5]

            if nice_eligible:
                self.nice_leaderboard.append(new_score)
                self.nice_leaderboard.sort(key=lambda x: x.score)
                self.nice_leaderboard = self.nice_leaderboard[:5]
            
            self.save_leaderboard()
            return time.time()
        
        return last_debounce

    def update_name(self, identifier: str, name: str) -> bool:
        for score in self.threat_leaderboard + self.nice_leaderboard:
            if score.id == identifier:
                score.name = name
                self.save_leaderboard()
                return True
        return False
