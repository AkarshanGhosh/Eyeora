# db/startup/create_indexes.py
async def create_indexes(db):
    """Create all necessary database indexes"""
    
    # Users collection
    try:
        # Drop existing email index if it has wrong name
        try:
            await db.users.drop_index("uniq_email")
        except:
            pass
        
        # Create email index with correct name
        await db.users.create_index("email", unique=True, name="email_1")
    except Exception as e:
        # Index might already exist with correct name
        if "already exists" not in str(e):
            print(f"⚠️  Users email index: {e}")
    
    try:
        await db.users.create_index("created_at", name="created_at_1")
    except Exception as e:
        if "already exists" not in str(e):
            print(f"⚠️  Users created_at index: {e}")
    
    try:
        await db.users.create_index("role", name="role_1")
    except Exception as e:
        if "already exists" not in str(e):
            print(f"⚠️  Users role index: {e}")
    
    # Cameras collection
    try:
        await db.cameras.create_index("uid", unique=True, name="uid_1")
    except Exception as e:
        if "already exists" not in str(e):
            print(f"⚠️  Cameras uid index: {e}")
    
    try:
        await db.cameras.create_index("is_active", name="is_active_1")
    except Exception as e:
        if "already exists" not in str(e):
            print(f"⚠️  Cameras is_active index: {e}")
    
    try:
        await db.cameras.create_index("location", name="location_1")
    except Exception as e:
        if "already exists" not in str(e):
            print(f"⚠️  Cameras location index: {e}")
    
    # Active sessions collection
    try:
        await db.active_sessions.create_index("user_id", unique=True, name="user_id_1")
    except Exception as e:
        if "already exists" not in str(e):
            print(f"⚠️  Sessions user_id index: {e}")
    
    try:
        await db.active_sessions.create_index("last_activity", name="last_activity_1")
    except Exception as e:
        if "already exists" not in str(e):
            print(f"⚠️  Sessions last_activity index: {e}")
    
    print("✅ Database indexes created/verified")