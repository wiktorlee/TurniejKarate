from repositories.ranking_repository import RankingRepository
from collections import defaultdict
from typing import Dict

class RankingService:
    """Serwis dla rankingów"""
    
    def __init__(self):
        self.ranking_repo = RankingRepository()
    
    def get_rankings(self) -> Dict:
        """
        Pobiera wszystkie rankingi.
        Używa widoku v_results_with_users z Supabase - BEZ ZMIAN!
        """
        # 1. Ranking Klubowy
        club_rows = self.ranking_repo.get_club_ranking()
        club_ranking = []
        for idx, row in enumerate(club_rows, 1):
            club_ranking.append({"place": idx, "name": row[0], "points": row[1]})
        
        # 2. Ranking Narodowościowy
        nation_rows = self.ranking_repo.get_nation_ranking()
        nation_ranking = []
        for idx, row in enumerate(nation_rows, 1):
            nation_ranking.append({"place": idx, "name": row[0], "points": row[1]})
        
        # 3. Ranking Indywidualny per Kategoria
        indiv_rows = self.ranking_repo.get_individual_ranking()
        individual_ranking = defaultdict(list)
        
        for row in indiv_rows:
            cat_name = row[0]
            player_data = {
                "first_name": row[1],
                "last_name": row[2],
                "club": row[3],
                "country": row[4],
                "points": row[5]
            }
            individual_ranking[cat_name].append(player_data)
        
        # Dodaj miejsca wewnątrz każdej kategorii
        for cat in individual_ranking:
            for idx, player in enumerate(individual_ranking[cat], 1):
                player["place"] = idx
        
        # Konwertuj defaultdict na dict dla JSON
        individual_ranking_dict = dict(individual_ranking)
        
        return {
            "club_ranking": club_ranking,
            "nation_ranking": nation_ranking,
            "individual_ranking": individual_ranking_dict
        }


