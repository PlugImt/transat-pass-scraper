import logging
import requests
from api_client import ApiClient
from datetime import datetime

# Set up a logger for this module. It will inherit the root logger's configuration.
logger = logging.getLogger(__name__)

def step8_submit_to_api(planning, user_email: str, api_client: ApiClient):
    """
    Sends each course in the planning list to the API for a specific user.

    Args:
        planning (list): List of final, optimized course dictionaries.
        user_email (str): The email address of the user whose planning it is.
        api_client (ApiClient): An authenticated instance of the ApiClient.

    Returns:
        bool: True if all courses were sent successfully, False otherwise.
    """
    if not planning:
        logger.info(f"No planning data to send to API for user {user_email}.")
        return True

    logger.info(f"Step 8: Sending {len(planning)} courses to API for user {user_email}.")
    
    success_count = 0
    failure_count = 0

    for course in planning:
        # Create a copy to avoid modifying the original course object.
        course_payload = course.copy()

        course_payload["user_email"] = user_email

        # The API expects start_time and end_time as ISO 8601 strings.
        if isinstance(course_payload.get('start_time'), datetime):
            course_payload['start_time'] = course_payload['start_time'].isoformat()
        if isinstance(course_payload.get('end_time'), datetime):
            course_payload['end_time'] = course_payload['end_time'].isoformat()
            
        try:
            api_client.post_course(course_payload)
            success_count += 1
        except requests.exceptions.RequestException as e:
            logger.error(f"API Error sending course for user {user_email}: {course_payload} | Error: {e}")
            failure_count += 1
        except Exception as e:
            logger.error(f"Unexpected error sending course to API: {course_payload} | Error: {e}")
            failure_count += 1

    logger.info(f"Step 8 Finished: Successfully sent {success_count}/{len(planning)} courses for user {user_email}.")
    
    return failure_count == 0