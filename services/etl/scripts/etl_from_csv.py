#!/usr/bin/env python3
"""
Load fighter and fight data from CSV files into FightMatch database.
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("Error: DATABASE_URL environment variable not set")
    sys.exit(1)


def load_fighters_from_csv(cursor, csv_path: Path):
    """Load fighters from CSV."""
    print(f"Loading fighters from {csv_path}...")
    
    df = pd.read_csv(csv_path)
    
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO fighters (slug, name, ufcstats_id, date_of_birth, height_inches, reach_inches, stance)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (slug) DO UPDATE SET
                name = EXCLUDED.name,
                ufcstats_id = EXCLUDED.ufcstats_id,
                date_of_birth = EXCLUDED.date_of_birth,
                height_inches = EXCLUDED.height_inches,
                reach_inches = EXCLUDED.reach_inches,
                stance = EXCLUDED.stance
        """, (
            row.get('slug'),
            row.get('name'),
            row.get('ufcstats_id'),
            row.get('date_of_birth'),
            row.get('height_inches'),
            row.get('reach_inches'),
            row.get('stance'),
        ))
    
    print(f"Loaded {len(df)} fighters")


def load_fights_from_csv(cursor, csv_path: Path):
    """Load fights from CSV."""
    print(f"Loading fights from {csv_path}...")
    
    df = pd.read_csv(csv_path)
    
    for _, row in df.iterrows():
        # Get event_id if event name is provided
        event_id = None
        if row.get('event_name'):
            cursor.execute("SELECT id FROM events WHERE name = %s", (row['event_name'],))
            result = cursor.fetchone()
            if result:
                event_id = result[0]
        
        # Get weight_class_id
        weight_class_id = None
        if row.get('weight_class_slug'):
            cursor.execute("SELECT id FROM weight_classes WHERE slug = %s", (row['weight_class_slug'],))
            result = cursor.fetchone()
            if result:
                weight_class_id = result[0]
        
        cursor.execute("""
            INSERT INTO fights (event_id, date, weight_class_id, result_type, result_method, result_round, result_time, ufcstats_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ufcstats_id) DO UPDATE SET
                event_id = EXCLUDED.event_id,
                date = EXCLUDED.date,
                weight_class_id = EXCLUDED.weight_class_id,
                result_type = EXCLUDED.result_type,
                result_method = EXCLUDED.result_method,
                result_round = EXCLUDED.result_round,
                result_time = EXCLUDED.result_time
        """, (
            event_id,
            row.get('date'),
            weight_class_id,
            row.get('result_type'),
            row.get('result_method'),
            row.get('result_round'),
            row.get('result_time'),
            row.get('ufcstats_id'),
        ))
    
    print(f"Loaded {len(df)} fights")


def load_participants_from_csv(cursor, csv_path: Path):
    """Load fight participants from CSV."""
    print(f"Loading participants from {csv_path}...")
    
    df = pd.read_csv(csv_path)
    
    for _, row in df.iterrows():
        # Get fight_id
        fight_id = None
        if row.get('fight_ufcstats_id'):
            cursor.execute("SELECT id FROM fights WHERE ufcstats_id = %s", (row['fight_ufcstats_id'],))
            result = cursor.fetchone()
            if result:
                fight_id = result[0]
        
        # Get fighter_id
        fighter_id = None
        if row.get('fighter_slug'):
            cursor.execute("SELECT id FROM fighters WHERE slug = %s", (row['fighter_slug'],))
            result = cursor.fetchone()
            if result:
                fighter_id = result[0]
        
        if fight_id and fighter_id:
            cursor.execute("""
                INSERT INTO fight_participants (fight_id, fighter_id, is_winner, is_champion, weight_lbs)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (fight_id, fighter_id) DO UPDATE SET
                    is_winner = EXCLUDED.is_winner,
                    is_champion = EXCLUDED.is_champion,
                    weight_lbs = EXCLUDED.weight_lbs
            """, (
                fight_id,
                fighter_id,
                row.get('is_winner'),
                row.get('is_champion', False),
                row.get('weight_lbs'),
            ))
    
    print(f"Loaded {len(df)} participants")


def main():
    parser = argparse.ArgumentParser(description='Load data from CSV files')
    parser.add_argument('--fighters', type=Path, help='Path to fighters CSV')
    parser.add_argument('--fights', type=Path, help='Path to fights CSV')
    parser.add_argument('--participants', type=Path, help='Path to participants CSV')
    
    args = parser.parse_args()
    
    if not any([args.fighters, args.fights, args.participants]):
        print("Error: At least one CSV file must be provided")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        if args.fighters:
            load_fighters_from_csv(cursor, args.fighters)
        
        if args.fights:
            load_fights_from_csv(cursor, args.fights)
        
        if args.participants:
            load_participants_from_csv(cursor, args.participants)
        
        cursor.close()
        conn.close()
        
        print("CSV data loaded successfully!")
        
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

