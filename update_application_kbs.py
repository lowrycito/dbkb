#!/usr/bin/env python3
"""
Update application table with correct knowledge base IDs
"""
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import get_chat_db_connection

def update_epic_application_kbs():
    """Update Epic application with correct KB IDs"""
    print("🔧 Updating Epic application with correct KB IDs...")
    
    connection = get_chat_db_connection()
    if not connection:
        print("❌ Could not connect to database")
        return False
    
    try:
        cursor = connection.cursor()
        
        cursor.execute(
            """UPDATE application 
               SET DatabaseKnowledgeBaseId = %s, 
                   SupportKnowledgeBaseId = %s,
                   UpdatedAt = NOW()
               WHERE Name = 'epic' AND IsActive = TRUE""",
            ('KRD3MW7QFS', 'ECC3L7C2PG')
        )
        
        rows_affected = cursor.rowcount
        connection.commit()
        
        if rows_affected > 0:
            print(f"✅ Updated {rows_affected} Epic application record(s)")
            
            cursor.execute(
                "SELECT Name, DatabaseKnowledgeBaseId, SupportKnowledgeBaseId FROM application WHERE Name = 'epic'"
            )
            result = cursor.fetchone()
            
            if result:
                print(f"✅ Verified: Epic -> DB: {result[1]}, Support: {result[2]}")
            
            return True
        else:
            print("❌ No Epic application records found to update")
            return False
            
    except Exception as e:
        print(f"❌ Error updating application KBs: {e}")
        return False
    finally:
        if connection:
            connection.close()

def show_current_application_config():
    """Show current application table configuration"""
    print("📋 Current Application Configuration:")
    
    connection = get_chat_db_connection()
    if not connection:
        print("❌ Could not connect to database")
        return
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM application WHERE IsActive = TRUE ORDER BY Name")
        apps = cursor.fetchall()
        
        for app in apps:
            print(f"  {app['Name']}: DB={app['DatabaseKnowledgeBaseId']}, Support={app['SupportKnowledgeBaseId']}")
            
    except Exception as e:
        print(f"❌ Error reading application config: {e}")
    finally:
        if connection:
            connection.close()

def main():
    print("🚀 Application KB Configuration Update")
    print("=" * 50)
    
    show_current_application_config()
    
    print("\n" + "=" * 50)
    success = update_epic_application_kbs()
    
    if success:
        print("\n📋 Updated Application Configuration:")
        show_current_application_config()
    else:
        print("\n❌ Update failed")

if __name__ == "__main__":
    main()
