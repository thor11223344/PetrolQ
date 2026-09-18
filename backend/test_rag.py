import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import SyntheticEvent
from main import compute_cosine_similarity
from simulator import get_well_region_tag
from nlp.config import get_embedding

def test_search():
    db = SessionLocal()
    try:
        all_events = db.query(SyntheticEvent).all()
        print(f"Total events in DB: {len(all_events)}")
        
        query_text = "gas kicks and mud loss"
        target_region = get_well_region_tag("OIL-TENGAKHAT-1")
        well_id = "OIL-TENGAKHAT-1"
        depth_tvd = None
        
        q_vec = get_embedding(query_text)
        
        scored_events = []
        for ev in all_events:
            if ev.embedding:
                score = compute_cosine_similarity(q_vec, ev.embedding)
                ev_region = get_well_region_tag(str(ev.well_id or ""))
                if ev_region == target_region:
                    score += 0.15
                if well_id and ev.well_id == well_id:
                    score += 0.10
                
                scored_events.append((score, ev))
        
        # Original sort
        scored_events.sort(key=lambda x: (x[0], getattr(x[1], 'id', 0) if isinstance(getattr(x[1], 'id', 0), int) else 0), reverse=True)
        
        print("Top 10 events:")
        for score, ev in scored_events[:10]:
            print(f"ID: {ev.id}, Score: {score:.4f}, Well: {ev.well_id}, Type: {ev.event_type}, Cause: {ev.root_cause}")
            
    finally:
        db.close()

if __name__ == "__main__":
    test_search()
