from datetime import timedelta
import logging

# Set up a logger for this module. It will inherit the root logger's configuration.
logger = logging.getLogger(__name__)

def step7_optimize_planning(planning_data, max_break_minutes=30):
    """
    Optimizes a list of planning events by merging consecutive courses.

    Two courses are merged if they have the same title, teacher, room, and group,
    and the time gap between them is less than or equal to max_break_minutes.

    Args:
        planning_data (list): A list of course dictionaries. Each dict must have
                              'start_time', 'end_time' (as datetime objects),
                              'title', 'teacher', 'room', 'group', and 'date'.
        max_break_minutes (int): The maximum duration of a break (in minutes)
                                 for two courses to be considered consecutive.

    Returns:
        list: A new list of course dictionaries with consecutive events merged.
    """
    if not planning_data or len(planning_data) < 2:
        logger.info("Planning has less than 2 entries, no optimization needed.")
        return planning_data

    # Sort the planning chronologically by start_time.
    try:
        sorted_planning = sorted(planning_data, key=lambda x: x['start_time'])
    except (TypeError, KeyError) as e:
        logger.error(f"Could not sort planning data. Missing or invalid 'start_time'. Error: {e}")
        # Return original data if sorting fails to prevent data loss.
        return planning_data

    merged_planning = []
    
    # Use an iterator to easily manage the flow, which is more efficient than indexing.
    planning_iterator = iter(sorted_planning)
    
    # Get the first course to start the process.
    current_course = next(planning_iterator)

    for next_course in planning_iterator:
        # Define what makes two courses identical (ignoring time).
        is_same_course = (
            current_course['title'] == next_course['title'] and
            current_course['teacher'] == next_course['teacher'] and
            current_course['room'] == next_course['room'] and
            current_course['group'] == next_course['group'] and
            current_course['date'] == next_course['date'] # Ensures we don't merge across days.
        )

        # Check if they are consecutive within the allowed break time.
        time_gap = next_course['start_time'] - current_course['end_time']
        is_consecutive = timedelta(minutes=0) <= time_gap <= timedelta(minutes=max_break_minutes)

        # If same and consecutive, merge them by updating the end_time.
        if is_same_course and is_consecutive:
            logger.info(
                f"Merging course '{current_course['title']}' on {current_course['date']}. "
                f"Extending end time from {current_course['end_time'].strftime('%H:%M')} "
                f"to {next_course['end_time'].strftime('%H:%M')}."
            )
            # Update the end time of the current block to the end time of the next block.
            current_course['end_time'] = next_course['end_time']
        else:
            # If not mergeable, the current_course block is finished. Add it to our results.
            merged_planning.append(current_course)
            # The next_course becomes the new current_course to check against.
            current_course = next_course

    # The loop finishes, but the very last course block is still in `current_course`. Add it.
    merged_planning.append(current_course)
    
    original_count = len(planning_data)
    final_count = len(merged_planning)
    if final_count < original_count:
        logger.info(f"Planning optimization complete. Reduced from {original_count} to {final_count} entries.")

    return merged_planning