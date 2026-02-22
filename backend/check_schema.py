from database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
columns = inspector.get_columns('surowce')

print("Columns in 'surowce' table:")
print("=" * 50)
for col in columns:
    print(f"{col['name']:30} {col['type']}")
