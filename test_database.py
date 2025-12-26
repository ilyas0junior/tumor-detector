# test_database.py
from utils.database import init_database, get_statistics

# Initialize
init_database()

# Get stats
stats = get_statistics()
print(f"Total cases: {stats['total_cases']}")
print(f"Average confidence: {stats['avg_confidence']:.2%}")

if stats['stage_distribution']:
    print("\nStage distribution:")
    for stage, count in stats['stage_distribution'].items():
        print(f"  {stage}: {count}")