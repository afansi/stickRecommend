from sqlmodel import Session, select, delete
from database import engine
from models.tables import Recommendation, DiscoveryOpportunity
import math

def fix_db():
    with Session(engine) as session:
        print("Fixing Recommendations with NaN rs_rating...")
        recs = session.exec(select(Recommendation)).all()
        fixed_count = 0
        for r in recs:
            if r.rs_rating is not None and math.isnan(r.rs_rating):
                r.rs_rating = 50.0 # Default value
                session.add(r)
                fixed_count += 1
        
        session.commit()
        print(f"Fixed {fixed_count} recommendations.")

if __name__ == "__main__":
    fix_db()
