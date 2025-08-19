# import logging
# from typing import Optional, Dict, Any, Union
# from sqlalchemy.orm import Session
# from sqlalchemy import desc
# from datetime import datetime, date, UTC
# from rich import print
# from models.database_models import Checkin, User, ChatSummary


# logger = logging.getLogger(__name__)

# class DatabaseService:
#     """Service class for database operations related to check-ins"""
    
#     @staticmethod
#     def get_last_daily_checkin(
#         db: Session, 
#         user_id: int, 
#         is_morning: bool
#     ) -> Optional[Dict[str, Any]]:
#         """
#         Get the last daily checkin for a user based on AM/PM boolean
#         Includes user information (name, gender, age) by joining with User table
        
#         Args:
#             db: Database session
#             user_id: ID of the user
#             is_morning: Boolean - True for morning (AM), False for evening (PM)
            
#         Returns:
#             Dictionary containing checkin data + user context or None if not found
#         """
#         try:
#             # Determine checkin type based on boolean
#             checkin_type = "morning" if is_morning else "evening"
            
#             # Query for the most recent checkin with user information using JOIN
#             # Using select_from for better performance and explicit column selection
#             # Added limit(1) for additional optimization
#             last_checkin_with_user = db.query(
#                 Checkin.sleep_quality, Checkin.body_sensation, Checkin.energy_level,
#                 Checkin.mental_state, Checkin.executive_task, Checkin.emotion_category,
#                 Checkin.overwhelm_amount, Checkin.emotion_in_moment, Checkin.surroundings_impact,
#                 Checkin.meaningful_moments_quantity, Checkin.checkin_time,
#                 User.first_name, User.last_name, User.age, User.gender
#             ).select_from(Checkin)\
#                 .join(User, Checkin.user_id == User.id)\
#                 .filter(Checkin.user_id == user_id)\
#                 .filter(Checkin.checkin_type == checkin_type)\
#                 .order_by(desc(Checkin.checkin_time))\
#                 .limit(1)\
#                 .first()
            
#             if not last_checkin_with_user:
#                 logger.info(f"No {checkin_type} checkin found for user {user_id}")
#                 return None
            
#             # Unpack the result (now it's a tuple of selected columns)
#             result = last_checkin_with_user
            
#             # Prepare response based on checkin type
#             if is_morning:
#                 # Morning checkin data
#                 checkin_data = {
#                     "sleep_quality": result.sleep_quality,
#                     "body_sensation": result.body_sensation,
#                     "energy_level": result.energy_level,
#                     "mental_state": result.mental_state,
#                     "executive_task": result.executive_task
#                 }
#             else:
#                 # Evening checkin data
#                 checkin_data = {
#                     "emotion_category": result.emotion_category,
#                     "overwhelm_amount": result.overwhelm_amount,
#                     "emotion_in_moment": result.emotion_in_moment,
#                     "surroundings_impact": result.surroundings_impact,
#                     "meaningful_moments_quantity": result.meaningful_moments_quantity
#                 }
            
#             # Add user context information
#             user_context = {
#                 "first_name": result.first_name,
#                 "last_name": result.last_name,
#                 "age": result.age,
#                 "gender": DatabaseService._get_gender_text(result.gender)
#             }
            
#             # Combine checkin data with user context
#             complete_context = {
#                 **checkin_data,
#                 **user_context
#             }
            
#             logger.info(f"Retrieved last {checkin_type} checkin with user context for user {user_id}")
#             return complete_context
            
#         except Exception as e:
#             logger.error(f"Error retrieving last {checkin_type} checkin for user {user_id}: {e}")
#             return None
    
#     @staticmethod
#     def _get_gender_text(gender: int) -> str:
#         """Convert gender number to readable text"""
#         gender_map = {
#             0: "Male",
#             1: "Female", 
#             2: "Third gender"
#         }
#         return gender_map.get(gender, "Not specified")
    
#     @staticmethod
#     def get_today_checkins(db: Session, user_id: int) -> Dict[str, Any]:
#         """
#         Get today's checkins for a user (both morning and evening)
        
#         Args:
#             db: Database session
#             user_id: ID of the user
            
#         Returns:
#             Dictionary containing today's checkins
#         """
#         try:
#             today = date.today()
            
#             today_checkins = db.query(Checkin)\
#                 .filter(Checkin.user_id == user_id)\
#                 .filter(Checkin.checkin_time >= today)\
#                 .order_by(Checkin.checkin_time.asc())\
#                 .all()
            
#             morning_checkin = None
#             evening_checkin = None
            
#             for checkin in today_checkins:
#                 if checkin.checkin_type == "morning":
#                     morning_checkin = {
#                         "id": checkin.id,
#                         "checkin_time": checkin.checkin_time.isoformat(),
#                         "sleep_quality": checkin.sleep_quality,
#                         "body_sensation": checkin.body_sensation,
#                         "energy_level": checkin.energy_level,
#                         "mental_state": checkin.mental_state,
#                         "executive_task": checkin.executive_task
#                     }
#                 elif checkin.checkin_type == "evening":
#                     evening_checkin = {
#                         "id": checkin.id,
#                         "checkin_time": checkin.checkin_time.isoformat(),
#                         "emotion_category": checkin.emotion_category,
#                         "overwhelm_amount": checkin.overwhelm_amount,
#                         "emotion_in_moment": checkin.emotion_in_moment,
#                         "surroundings_impact": checkin.surroundings_impact,
#                         "meaningful_moments_quantity": checkin.meaningful_moments_quantity
#                     }
            
#             return {
#                 "user_id": user_id,
#                 "date": today.isoformat(),
#                 "morning_checkin": morning_checkin,
#                 "evening_checkin": evening_checkin,
#                 "total_checkins": len(today_checkins)
#             }
            
#         except Exception as e:
#             logger.error(f"Error retrieving today's checkins for user {user_id}: {e}")
#             return {
#                 "user_id": user_id,
#                 "date": today.isoformat(),
#                 "morning_checkin": None,
#                 "evening_checkin": None,
#                 "total_checkins": 0,
#                 "error": str(e)
#             }
    
#     @staticmethod
#     def get_checkin_history(
#         db: Session, 
#         user_id: int, 
#         checkin_type: Optional[str] = None,
#         limit: int = 30
#     ) -> Dict[str, Any]:
#         """
#         Get checkin history for a user with optional type filtering
        
#         Args:
#             db: Database session
#             user_id: ID of the user
#             checkin_type: Optional filter for "morning" or "evening"
#             limit: Maximum number of checkins to return
            
#         Returns:
#             Dictionary containing checkin history
#         """
#         try:
#             query = db.query(Checkin).filter(Checkin.user_id == user_id)
            
#             if checkin_type:
#                 query = query.filter(Checkin.checkin_type == checkin_type)
            
#             checkins = query.order_by(desc(Checkin.checkin_time)).limit(limit).all()
            
#             checkin_list = []
#             for checkin in checkins:
#                 checkin_data = {
#                     "id": checkin.id,
#                     "checkin_type": checkin.checkin_type,
#                     "checkin_time": checkin.checkin_time.isoformat(),
#                     "user_id": checkin.user_id
#                 }
                
#                 # Add type-specific data
#                 if checkin.checkin_type == "morning":
#                     checkin_data.update({
#                         "sleep_quality": checkin.sleep_quality,
#                         "body_sensation": checkin.body_sensation,
#                         "energy_level": checkin.energy_level,
#                         "mental_state": checkin.mental_state,
#                         "executive_task": checkin.executive_task
#                     })
#                 else:  # evening
#                     checkin_data.update({
#                         "emotion_category": checkin.emotion_category,
#                         "overwhelm_amount": checkin.overwhelm_amount,
#                         "emotion_in_moment": checkin.emotion_in_moment,
#                         "surroundings_impact": checkin.surroundings_impact,
#                         "meaningful_moments_quantity": checkin.meaningful_moments_quantity
#                     })
                
#                 checkin_list.append(checkin_data)
            
#             return {
#                 "user_id": user_id,
#                 "checkin_type": checkin_type,
#                 "checkins": checkin_list,
#                 "total_count": len(checkin_list),
#                 "limit": limit
#             }
            
#         except Exception as e:
#             logger.error(f"Error retrieving checkin history for user {user_id}: {e}")
#             return {
#                 "user_id": user_id,
#                 "checkin_type": checkin_type,
#                 "checkins": [],
#                 "total_count": 0,
#                 "limit": limit,
#                 "error": str(e)
#             }

#     @staticmethod
#     def save_chat_summary(
#         db: Session,
#         user_id: int,
#         chat_id: str,
#         summary: str
#     ) -> Optional[Dict[str, Any]]:
#         """
#         Save a chat summary to the database
        
#         Args:
#             db: Database session
#             user_id: ID of the user
#             chat_id: The chat identifier
#             summary: The generated summary text
            
#         Returns:
#             Dictionary containing the saved summary data or None if failed
#         """
#         try:
#             # Check if a summary already exists for this chat_id
#             existing_summary = db.query(ChatSummary).filter(
#                 ChatSummary.chat_id == chat_id
#             ).first()
            
#             if existing_summary:
#                 # Update existing summary
#                 existing_summary.summary = summary
#                 existing_summary.updated_at = datetime.now(UTC)
#                 db.commit()
#                 logger.info(f"Updated existing chat summary for chat_id: {chat_id}")
                
#                 return {
#                     "id": existing_summary.id,
#                     "user_id": existing_summary.user_id,
#                     "chat_id": existing_summary.chat_id,
#                     "summary": existing_summary.summary,
#                     "updated_at": existing_summary.updated_at.isoformat()
#                 }
#             else:
#                 # Create new summary
#                 new_summary = ChatSummary(
#                     user_id=user_id,
#                     chat_id=chat_id,
#                     summary=summary
#                 )
#                 db.add(new_summary)
#                 db.commit()
#                 db.refresh(new_summary)
                
#                 logger.info(f"Created new chat summary for chat_id: {chat_id}")
                
#                 return {
#                     "id": new_summary.id,
#                     "user_id": new_summary.user_id,
#                     "chat_id": new_summary.chat_id,
#                     "summary": new_summary.summary,
#                     "created_at": new_summary.created_at.isoformat()
#                 }
                
#         except Exception as e:
#             logger.error(f"Error saving chat summary for user {user_id}, chat {chat_id}: {e}")
#             db.rollback()
#             return None

#     @staticmethod
#     def get_chat_summary(
#         db: Session,
#         chat_id: str
#     ) -> Optional[Dict[str, Any]]:
#         """
#         Retrieve a chat summary by chat_id
        
#         Args:
#             db: Database session
#             chat_id: The chat identifier
            
#         Returns:
#             Dictionary containing the summary data or None if not found
#         """
#         try:
#             summary = db.query(ChatSummary).filter(
#                 ChatSummary.chat_id == chat_id
#             ).first()
            
#             if not summary:
#                 logger.info(f"No chat summary found for chat_id: {chat_id}")
#                 return None
            
#             return {
#                 "id": summary.id,
#                 "user_id": summary.user_id,
#                 "chat_id": summary.chat_id,
#                 "summary": summary.summary,
#                 "created_at": summary.created_at.isoformat(),
#                 "updated_at": summary.updated_at.isoformat()
#             }
            
#         except Exception as e:
#             logger.error(f"Error retrieving chat summary for chat_id {chat_id}: {e}")
#             return None

#     @staticmethod
#     def get_user_chat_summaries(
#         db: Session,
#         user_id: int,
#         limit: int = 50
#     ) -> Dict[str, Any]:
#         """
#         Get all chat summaries for a specific user
        
#         Args:
#             db: Database session
#             user_id: ID of the user
#             limit: Maximum number of summaries to return
            
#         Returns:
#             Dictionary containing user's chat summaries
#         """
#         try:
#             summaries = db.query(ChatSummary)\
#                 .filter(ChatSummary.user_id == user_id)\
#                 .order_by(desc(ChatSummary.created_at))\
#                 .limit(limit)\
#                 .all()
            
#             summary_list = []
#             for summary in summaries:
#                 summary_list.append({
#                     "id": summary.id,
#                     "chat_id": summary.chat_id,
#                     "summary": summary.summary,
#                     "created_at": summary.created_at.isoformat(),
#                     "updated_at": summary.updated_at.isoformat()
#                 })
            
#             return {
#                 "user_id": user_id,
#                 "summaries": summary_list,
#                 "total_count": len(summary_list),
#                 "limit": limit
#             }
            
#         except Exception as e:
#             logger.error(f"Error retrieving chat summaries for user {user_id}: {e}")
#             return {
#                 "user_id": user_id,
#                 "summaries": [],
#                 "total_count": 0,
#                 "limit": limit,
#                 "error": str(e)
#             }

#     @staticmethod
#     def delete_chat_summary(
#         db: Session,
#         chat_id: str,
#         user_id: int
#     ) -> bool:
#         """
#         Delete a chat summary (only if it belongs to the user)
        
#         Args:
#             db: Database session
#             chat_id: The chat identifier
#             user_id: ID of the user (for authorization)
            
#         Returns:
#             True if deleted successfully, False otherwise
#         """
#         try:
#             summary = db.query(ChatSummary).filter(
#                 ChatSummary.chat_id == chat_id,
#                 ChatSummary.user_id == user_id
#             ).first()
            
#             if not summary:
#                 logger.warning(f"No chat summary found for chat_id: {chat_id} and user: {user_id}")
#                 return False
            
#             db.delete(summary)
#             db.commit()
            
#             logger.info(f"Deleted chat summary for chat_id: {chat_id}")
#             return True
            
#         except Exception as e:
#             logger.error(f"Error deleting chat summary for chat_id {chat_id}: {e}")
#             db.rollback()
#             return False

# if __name__ == "__main__":
#     # Use get_db() function for proper session management
#     db = next(get_db())
#     result = DatabaseService.get_last_daily_checkin(db, 2, True)
#     print(result)
