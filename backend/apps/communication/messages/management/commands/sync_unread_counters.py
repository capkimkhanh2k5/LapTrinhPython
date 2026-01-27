from django.core.management.base import BaseCommand
from apps.communication.message_participants.models import MessageParticipant
from apps.communication.messages.services.mongo_service import MongoChatService
from django.conf import settings
import pymongo
from datetime import datetime

class Command(BaseCommand):
    help = 'Sync unread counters from SQL/Mongo messages to unread_counters collection'

    def handle(self, *args, **options):
        client = pymongo.MongoClient(settings.MONGO_URI)
        db = client[settings.MONGO_DB_NAME]
        messages_col = db['messages']
        counters_col = db['unread_counters']
        
        # Clear existing counters? Or just upsert?
        # Upsert is safer.
        
        self.stdout.write("Starting sync...")
        
        participants = MessageParticipant.objects.filter(is_active=True).select_related('thread', 'user')
        
        count_updated = 0
        total = participants.count()
        
        for idx, p in enumerate(participants):
            thread_id = p.thread.id
            user_id = p.user.id
            last_read_at = p.last_read_at
            
            # Count messages in Mongo created after last_read_at
            # Exclude messages sent by self? Usually unread is for received messages.
            # Yes, standard logic: unread = received messages > read_time.
            # But in group chat, it's any message > read_time.
            # Excluding self: query should be {"sender_id": {"$ne": user_id}}
            
            query = {
                "thread_id": thread_id,
                "sender_id": {"$ne": user_id}
            }
            
            if last_read_at:
                query["created_at"] = {"$gt": last_read_at}
                
            unread_count = messages_col.count_documents(query)
            
            # Update counter
            if unread_count > 0:
                counters_col.update_one(
                    {"user_id": user_id, "thread_id": thread_id},
                    {
                        "$set": {
                            "count": unread_count,
                            "last_updated": datetime.utcnow()
                        }
                    },
                    upsert=True
                )
                count_updated += 1
            else:
                 # Ensure it's 0 if no unread
                 counters_col.update_one(
                    {"user_id": user_id, "thread_id": thread_id},
                    {
                        "$set": {
                            "count": 0,
                            "last_updated": datetime.utcnow()
                        }
                    },
                    upsert=True
                )
            
            if idx % 100 == 0:
                self.stdout.write(f"Processed {idx}/{total} participants...")

        self.stdout.write(self.style.SUCCESS(f"Successfully synced unread counters. Updated {count_updated} records."))
