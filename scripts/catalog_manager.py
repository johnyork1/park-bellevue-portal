#!/usr/bin/env python3
"""
Park Bellevue Collective - Catalog Manager
Shares the SAME catalog.json as the main Ridgemont Studio Manager
"""
import json
import glob
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# IMPORTANT: Points to the SAME data folder as main Ridgemont Manager
DATA_DIR = Path(__file__).parent.parent.parent / "Ridgemont Catalog Manager" / "data"
BACKUPS_DIR = Path(__file__).parent.parent / "backups"

# Writer splits for Park Bellevue (John York + Ron Queensbury)
DEFAULT_SPLITS = {
    "PARK_BELLEVUE": [{"writer_id": "W-0001", "percentage": 50}, {"writer_id": "W-0003", "percentage": 50}],
}

class CatalogManager:
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = Path(data_dir)
        self.catalog = {"songs": []}
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        self._load_data()

    def _load_data(self):
        catalog_path = self.data_dir / "catalog.json"
        if catalog_path.exists():
            with open(catalog_path, 'r') as f:
                self._full_catalog = json.load(f)
                # Filter to only Park Bellevue songs
                self.catalog = {
                    "songs": [s for s in self._full_catalog.get("songs", []) if s.get("act_id") == "PARK_BELLEVUE"]
                }
        else:
            self.catalog = {"songs": []}
            self._full_catalog = {"songs": []}

    def _backup_data(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUPS_DIR / f"catalog_backup_{timestamp}.json"
        with open(backup_path, 'w') as f:
            json.dump(self._full_catalog, f, indent=2, default=str)
        # Keep only last 10 backups
        backups = sorted(glob.glob(str(BACKUPS_DIR / "catalog_backup_*.json")))
        while len(backups) > 10:
            os.remove(backups.pop(0))
        return str(backup_path)

    def save_data(self):
        """Save changes back to the shared catalog."""
        try:
            self._backup_data()
        except:
            pass

        catalog_path = self.data_dir / "catalog.json"

        # Update the full catalog with our changes
        # Remove all PARK_BELLEVUE songs from full catalog
        other_songs = [s for s in self._full_catalog.get("songs", []) if s.get("act_id") != "PARK_BELLEVUE"]

        # Add back our (possibly modified) Park Bellevue songs
        self._full_catalog["songs"] = other_songs + self.catalog["songs"]

        with open(catalog_path, 'w') as f:
            json.dump(self._full_catalog, f, indent=2, default=str)
        print(f"✅ Data saved to {catalog_path}")

    def get_catalog_summary(self) -> Dict:
        songs = self.catalog.get("songs", [])
        by_status = {}
        for s in songs:
            status = s.get('status', 'unknown')
            by_status[status] = by_status.get(status, 0) + 1
        return {
            "total_songs": len(songs),
            "by_status": by_status,
            "by_act": {"PARK_BELLEVUE": len(songs)}
        }

    def get_revenue_summary(self) -> Dict:
        total = sum(s.get("revenue", {}).get("total_earned", 0) for s in self.catalog.get("songs", []))
        expenses = sum(
            sum(e.get('amount', 0) for e in s.get('revenue', {}).get('expenses', []))
            for s in self.catalog.get("songs", [])
        )
        return {"total_revenue": total, "total_expenses": expenses, "net_revenue": total - expenses}

    def find_song_by_title(self, title: str) -> Optional[Dict]:
        for s in self.catalog["songs"]:
            if s["title"].lower() == title.lower():
                return s
        return None

    def find_song_by_id(self, song_id: str) -> Optional[Dict]:
        for s in self.catalog["songs"]:
            if s["song_id"] == song_id:
                return s
        return None

    def update_song(self, song_id: str, updates: dict) -> bool:
        """Updates an existing song's details (status, deployments, ISRC, etc.)."""
        for song in self.catalog['songs']:
            if song['song_id'] == song_id:
                # Handle nested updates for registration info
                if 'registration' in updates:
                    if 'registration' not in song:
                        song['registration'] = {}
                    song['registration'].update(updates.pop('registration'))

                # Handle nested updates for deployments
                if 'deployments' in updates:
                    if 'deployments' not in song:
                        song['deployments'] = {"distribution": [], "sync_libraries": [], "streaming": []}
                    song['deployments'].update(updates.pop('deployments'))

                # Apply remaining updates
                song.update(updates)

                # Update timestamp
                if 'dates' not in song:
                    song['dates'] = {}
                song['dates']['last_modified'] = datetime.now().isoformat()

                self.save_data()
                return True
        return False

    def add_expense(self, song_id: str, amount: float, category: str) -> str:
        song = self.find_song_by_id(song_id)
        if not song:
            return "Song not found."
        if "revenue" not in song:
            song["revenue"] = {"expenses": [], "total_earned": 0}
        if "expenses" not in song["revenue"]:
            song["revenue"]["expenses"] = []
        song["revenue"]["expenses"].append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "amount": amount,
            "category": category
        })
        self.save_data()
        return f"💸 Logged ${amount} expense for {song['title']}."

    def add_revenue(self, song_id: str, amount: float, source: str) -> str:
        song = self.find_song_by_id(song_id)
        if not song:
            return "Song not found."
        if "revenue" not in song:
            song["revenue"] = {"expenses": [], "total_earned": 0}
        song["revenue"]["total_earned"] = song["revenue"].get("total_earned", 0) + amount
        self.save_data()
        return f"💰 Added ${amount} revenue for {song['title']} from {source}."


if __name__ == "__main__":
    manager = CatalogManager()
    print(f"Park Bellevue Catalog Manager Loaded")
    print(f"Data directory: {DATA_DIR}")
    print(f"Songs loaded: {len(manager.catalog['songs'])}")
