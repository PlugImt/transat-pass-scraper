import logging
import re
from datetime import date, timedelta
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from datetime import datetime
import os

# Set up a logger for this module. It will inherit the root logger's configuration.
logger = logging.getLogger(__name__)

# Helper function to get the list of Mondays of weeks to scrape.
def _get_mondays_to_scrape():
    """
    Generates a list of dates for the Monday of each week,
    from 4 weeks ago to 4 weeks from now (total of 9 weeks).
    """
    mondays = []
    today = date.today()
    # Find the Monday of the current week.
    current_monday = today - timedelta(days=today.weekday())
    
    # Loop from 4 weeks in the past to 4 weeks in the future.
    for i in range(-4, 5):
        monday_date = current_monday + timedelta(weeks=i)
        mondays.append(monday_date.strftime('%Y%m%d'))
        
    return mondays

# Helper function to parse a single week's planning page.
def _scrape_single_week(driver, timeout:int) -> list:
    """
    Scrapes the planning data for the currently displayed week.
    Assumes the driver is already inside the correct iframe.
    
    Returns:
        list: A list of course dictionaries for the week.
    """
    planning_of_the_week = []
    
    try:
        # Wait for the main planning table header to be visible.
        planning_header_xpath = "//td[@class='AuthentificationMenu' and contains(text(),'Agenda de l')]"
        header_element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, planning_header_xpath))
        )
        logger.info("Agenda planning table is visible. Starting to scrape.")
        
        # Extract month and year from the header.
        header_text = header_element.text
        month_year_match = re.search(r'([A-Za-zéû]+)\s+(\d{4})$', header_text.strip())
        if not month_year_match:
            logger.warning(f"Could not extract month/year from header: '{header_text}'")
            return []
            
        french_month, year = month_year_match.groups()
        month_map = {
            "Janvier": 1, "Février": 2, "Mars": 3, "Avril": 4, "Mai": 5, "Juin": 6, 
            "Juillet": 7, "Août": 8, "Septembre": 9, "Octobre": 10, "Novembre": 11, "Décembre": 12
        }
        month = month_map.get(french_month)
        if not month:
            logger.warning(f"Unrecognized month: {french_month}")
            return []

        # Get day headers.
        header_cells = driver.find_elements(By.XPATH, "//tr[contains(@class,'fondTresClair')]/td[position()>1]")
        days = []
        for i, cell in enumerate(header_cells):
            text = cell.text.strip().replace('\xa0', ' ')
            match = re.match(r"(\w+)\s+(\d{1,2})", text)
            if match:
                day_name, day_num = match.groups()
                # Handle month changeover (e.g., end of month)
                try:
                    full_date = datetime(int(year), month, int(day_num)).strftime("%Y-%m-%d")
                except ValueError:
                    logger.warning(f"Date parsing error for day {day_num} in month {month}. Skipping day.")
                    continue
                days.append((day_name, full_date))
            else:
                days.append((f"Day{i}", None))

        logger.info(f"Detected days for scraping are {days}.")
        # Traverse planning rows.
        rows_xpath = "//tr[td[@bgcolor='#DDDDDD']]"
        num_rows = len(driver.find_elements(By.XPATH, rows_xpath))
        logger.info(f"Found {num_rows} rows to process.")

        # Loop using an index (from 0 to num_rows-1).
        for i in range(num_rows):
            try:
                # Inside the loop, find the SPECIFIC row by its index.
                # XPath indexes are 1-based, so we use i + 1.
                # This re-acquires the element fresh on every single iteration.
                row = driver.find_element(By.XPATH, f"({rows_xpath})[{i+1}]")
                
                cells = row.find_elements(By.XPATH, "./td")
                if len(cells) < len(days) + 1: continue

                for j, (day_name, date_str) in enumerate(days):
                    if date_str is None: continue
                    
                    course_cell = cells[j + 1]

                    bgcolor = course_cell.get_attribute('bgcolor')
                    if not bgcolor or bgcolor.lower() == '#ededed':
                        continue

                    try:
                        # Check for the bold tag to confirm it's a course title cell.
                        title_element = course_cell.find_element(By.TAG_NAME, 'b')
                        title = title_element.text.strip().replace(' ', ' ')
                        
                        all_text_parts = course_cell.text.split('\n')
                        start_time_obj, end_time_obj, teachers, room, group = None, None, [], "", ""
                        
                        for part in all_text_parts:
                            time_match = re.search(r'(\d{2})H(\d{2})-(\d{2})H(\d{2})', part)
                            if time_match:
                                start_h, start_m, end_h, end_m = time_match.groups()
                                start_time_obj = datetime.strptime(f"{date_str} {start_h}:{start_m}", "%Y-%m-%d %H:%M")
                                end_time_obj = datetime.strptime(f"{date_str} {end_h}:{end_m}", "%Y-%m-%d %H:%M")

                            elif re.search(r"\bFISE|FIT|FIL|PROMO|GPE|ANNÉE|LV1|DEMI\b", part, re.IGNORECASE):
                                group = part

                            elif re.match(r"^[A-Z]{2,}-.*", part) or '(' in part:
                                room = part

                            elif part != title and re.fullmatch(r"[A-Z'’\s-]+ [A-Z][a-z'’-]+", part, re.IGNORECASE):
                                teachers.append(part)

                        if title and start_time_obj:
                            planning_of_the_week.append({
                                'date': date_str,
                                'title': title,
                                'start_time': start_time_obj,
                                'end_time': end_time_obj,
                                'teacher': ", ".join(teachers),
                                'room': room,
                                'group': group
                            })

                    except NoSuchElementException:
                        continue # Skip cells that are colored but have no title (e.g., rowspan continuation)
                    except Exception as e:
                        logger.warning(f"Error parsing course cell on {date_str}: {e}")

            # Catch the specific exception. If a row becomes stale even during this
            # short time, we can log it and safely continue to the next index.
            except StaleElementReferenceException:
                logger.warning(f"Row at index {i} became stale. Skipping.")
                continue
            except Exception as e:
                logger.warning(f"Failed to parse row at index {i}: {e}")

        return planning_of_the_week
    except Exception as e:
        logger.error(f"Critical error while scraping a single week: {e}", exc_info=True)
        return []

def step6_scrape_planning(driver, profile_url: str, timeout:int=30):
    """
    Navigates to a user's agenda and scrapes their planning for a 9-week period.
    Modifies the navigation arrow's onclick attribute and then clicks it.
    
    Args:
        driver: The Selenium WebDriver instance.
        profile_url (str): The URL of the user's profile page.
        timeout (int): Timeout for web driver waits.
        
    Returns:
        dict: A dictionary containing the scraped data or an error message.
    """
    try:
        logger.info(f"Step 6: Navigating to user planning page {profile_url}")
        driver.get(profile_url)
        time.sleep(5)

        if "Dossier.aspx?IdObjet=" not in driver.current_url:
            return {'error': f'Failed to navigate to user profile. URL: {driver.current_url}'}

        logger.info("On user profile page. Clicking 'Agenda' tab.")
        driver.switch_to.default_content()

        agenda_tab_xpath = "//nobr[text()='Agenda']/ancestor::table[contains(@onclick, 'ComponentArt_TabStrip_TabClick')]"
        try:
            WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, agenda_tab_xpath))).click()
            logger.info("Clicked the 'Agenda' tab.")
            time.sleep(5) 
        except TimeoutException:
            logger.error("Could not find or click the 'Agenda' tab.")
            return {'error': "Could not find or click the 'Agenda' tab."}

        logger.info("Switching to agenda iframe 'frm1'.")
        WebDriverWait(driver, timeout).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "frm1")))
        logger.info("Switched to iframe 'frm1'.")
        
        # Use the right arrow to navigate.
        # This also serves as our element to wait for after a page refresh.
        nav_arrow_xpath = "//*[@id='DivVis']/table/tbody/tr[1]/td[3]/a"

        logger.info("Waiting for initial agenda to load completely...")
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, nav_arrow_xpath))
        )
        logger.info("Initial agenda loaded. Starting weekly scrape.")

        mondays_to_scrape = _get_mondays_to_scrape()
        logger.info(f"Will scrape {len(mondays_to_scrape)} weeks, starting from Mondays: {mondays_to_scrape}")

        all_courses = []
        for i, monday_str in enumerate(mondays_to_scrape):
            logger.info(f"Scraping week {i+1}/{len(mondays_to_scrape)} (starting {monday_str})...")
            try:
                # Find the navigation arrow we will use.
                arrow_element = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.XPATH, nav_arrow_xpath))
                )

                # Use JavaScript to change the 'onclick' attribute to our desired date.
                js_change_attribute = f"arguments[0].setAttribute('onclick', \"NavDat('{monday_str}');return false;\");"
                driver.execute_script(js_change_attribute, arrow_element)
                logger.info(f"Set arrow's onclick to navigate to {monday_str}.")

                # Click the now-modified arrow to trigger the navigation.
                arrow_element.click()
                logger.info("Clicked the arrow to load the new week.")

                # Wait for the navigation to complete. We wait for the arrow 
                # to be present again after the refresh.
                # This prevents the "NavDat is not defined" or stale element errors.
                WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.XPATH, nav_arrow_xpath))
                )
                logger.info("New week's content has loaded. Stabilizing page...")
                # Add a small buffer for JS rendering, then dezoom/scroll to stabilize the view.
                time.sleep(1)
                try:
                    logger.info("De-zooming page and scrolling to ensure full visibility.")
                    driver.execute_script("document.body.style.zoom='100%'")
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(0.5)
                    driver.execute_script("window.scrollTo(0, 0);")
                except Exception as e:
                    logger.warning(f"Could not execute dezoom/scroll script: {e}")

                # Take a screenshot before scraping the week for debugging.
                try:
                    screenshot_dir = 'data/debug_screenshots'
                    os.makedirs(screenshot_dir, exist_ok=True)
                    screenshot_path = os.path.join(screenshot_dir, f'week_{monday_str}.png')
                    driver.get_screenshot_as_file(screenshot_path)
                    logger.info(f"Saved pre-scrape screenshot to {screenshot_path}")
                except Exception as e_ss:
                    logger.error(f"Could not save screenshot for week {monday_str}: {e_ss}")

            except Exception as nav_error:
                logger.error(f"Failed to navigate to week starting {monday_str}: {nav_error}", exc_info=True)
                continue 

            week_courses = _scrape_single_week(driver, timeout=timeout)
            if week_courses:
                all_courses.extend(week_courses)
        
        unique_planning = []
        seen = set()
        for d in all_courses:
            course_tuple = (d['date'], d['title'], d['teacher'], d['room'], d['group'], d['start_time'])
            if course_tuple not in seen:
                unique_planning.append(d)
                seen.add(course_tuple)
        
        logger.info(f"Found a total of {len(unique_planning)} unique course entries across all weeks.")
        
        return {
            'url': profile_url,
            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'planning': unique_planning
        }

    except Exception as e:
        logger.error(f"CRITICAL ERROR in step 6 (step6_scrape_planning): {e}", exc_info=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        error_screenshot_path = os.path.join('data', f'step6_error_{ts}.png')
        try:
            driver.get_screenshot_as_file(error_screenshot_path)
            logger.info(f"Saved error screenshot to {error_screenshot_path}")
        except Exception as e_ss:
            logger.error(f"Could not save error screenshot: {e_ss}")
        return {'error': str(e)}