from sqlmodel import Session, select
from database import engine
from models.tables import Recommendation, DiscoveryOpportunity
import math

def check_floats():
    with Session(engine) as session:
        print("Checking Recommendations...")
        recs = session.exec(select(Recommendation)).all()
        for r in recs:
            for field in ['suggested_entry', 'suggested_stop', 'suggested_target', 'rs_rating', 'confidence_score']:
                val = getattr(r, field)
                if val is not None and (math.isnan(val) or math.isinf(val)):
                    print(f"ERROR: Recommendation {r.id} ({r.ticker}) has {field}={val}")
        
        print("\nChecking DiscoveryOpportunities...")
        opps = session.exec(select(DiscoveryOpportunity)).all()
        for o in opps:
            for field in ['suggested_entry', 'suggested_stop', 'suggested_target', 'rs_rating']:
                val = getattr(o, field)
                if val is not None and (math.isnan(val) or math.isinf(val)):
                    print(f"ERROR: DiscoveryOpportunity {o.ticker} has {field}={val}")

if __name__ == "__main__":
    check_floats()
