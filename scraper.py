from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import time
import logging
import os
import requests
import re
from config import Config
from api_client import ApiClient
from datetime import datetime, timedelta

class TransatPassScraper:
    def __init__(self, headless=False, timeout=10):
        """
        Initialize the scraper
        
        Args:
            headless (bool): Run browser in headless mode
            timeout (int): Default timeout for waiting elements
        """
        self.timeout = timeout
        self.driver = None
        self.setup_logging()
        self.setup_driver(headless)

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def setup_driver(self, headless):
        """Setup Chrome WebDriver with options"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.maximize_window()
            self.logger.info("WebDriver initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def wait_and_click(self, locator_type, locator_value):
        """
        Wait for element and click it
        
        Args:
            locator_type: Type of locator (By.ID, By.XPATH, etc.)
            locator_value: Value of the locator
        """
        try:
            element = WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((locator_type, locator_value))
            )
            element.click()
            self.logger.info(f"Clicked element: {locator_value}")
            return True
        except TimeoutException:
            self.logger.error(f"Timeout waiting for clickable element: {locator_value}")
            return False
    
    def wait_and_send_keys(self, locator_type, locator_value, text):
        """
        Wait for element and send keys to it
        
        Args:
            locator_type: Type of locator
            locator_value: Value of the locator
            text: Text to send
        """
        try:
            element = WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((locator_type, locator_value))
            )
            element.clear()
            element.send_keys(text)
            self.logger.info(f"Sent text to element: {locator_value}")
            return True
        except TimeoutException:
            self.logger.error(f"Timeout waiting for element: {locator_value}")
            return False
        
    def step1_select_auth_mode(self):
        """
        Step 1: Navigate to login page and select authentication mode
        """
        try:
            self.logger.info("Step 1: Navigating to login page and selecting auth mode")
            
            # Navigate to the initial page
            self.driver.get("https://pass.imt-atlantique.fr/OpDotNet/Noyau/Login.aspx?")
            self.logger.info("Navigated to login page")
            
            # Wait for page to load
            time.sleep(2)
            
            # Click the remote auth button
            if self.wait_and_click(By.XPATH, '//*[@id="remoteAuth"]/button'):
                self.logger.info("Successfully selected remote authentication")
                time.sleep(2)  # Wait for page transition
                return True
            else:
                self.logger.error("Failed to click remote auth button")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in step 1: {e}")
            return False
    
    def step2_login(self, username, password):
        """
        Step 2: Enter username and password
        
        Args:
            username (str): Username for login
            password (str): Password for login
        """
        try:
            self.logger.info(f"Step 2: Entering login credentials (username: {username}, password: {password})")
            self.logger.info(f"Current URL before login: {self.driver.current_url}")
            
            # Wait for login form to appear
            time.sleep(3)
            
            # Check that we are on the correct CAS login URL
            current_url = self.driver.current_url
            if "https://cas.imt-atlantique.fr/cas/login?" not in current_url:
                self.logger.error(f"Not on CAS login page, current URL: {current_url}")
                return False
            
            # Fill username
            try:
                username_input = self.driver.find_element(By.XPATH, '//*[@id="username"]')
                username_input.clear()
                username_input.send_keys(username)
                self.logger.info(f"Filled username field with: {username}")
                self.logger.info(f"Current URL after filling username: {self.driver.current_url}")
            except Exception as e:
                self.logger.error(f"Could not find or fill username field: {e}. Current URL: {self.driver.current_url}")
                return False
            
            # Fill password
            try:
                password_input = self.driver.find_element(By.XPATH, '//*[@id="password"]')
                password_input.clear()
                password_input.send_keys(password)
                self.logger.info(f"Filled password field with: {password}")
                self.logger.info(f"Current URL after filling password: {self.driver.current_url}")
                # Try sending ENTER key to password field
                password_input.send_keys(Keys.RETURN)
                self.logger.info("Submitted login form by sending ENTER to password field.")
            except Exception as e:
                self.logger.error(f"Could not find or fill password field: {e}. Current URL: {self.driver.current_url}")
                return False
            
            time.sleep(2)
            self.logger.info(f"Current URL after submitting login: {self.driver.current_url}")
            
            # Check for error message
            try:
                msg_elem = self.driver.find_element(By.XPATH, '//*[@id="msg"]')
                if msg_elem.is_displayed() and msg_elem.text.strip():
                    self.logger.error(f"Login error message displayed: {msg_elem.text.strip()}. Current URL: {self.driver.current_url}")
                    return False
            except NoSuchElementException:
                self.logger.info("No login error message element found after submit (NoSuchElementException).")
            except Exception:
                self.logger.info("No login error message element found after submit.")
            
            # Wait for URL to change from CAS login page
            for i in range(20):  # up to 10 seconds
                new_url = self.driver.current_url
                if "cas.imt-atlantique.fr/cas/login" not in new_url:
                    self.logger.info(f"Left CAS login page, new URL: {new_url}")
                    break
                time.sleep(0.5)
            else:
                self.logger.warning(f"ENTER key did not submit form, trying to click submit button. Current URL: {self.driver.current_url}")
                try:
                    submit_btn = self.driver.find_element(By.XPATH, '//*[@id="fm1"]//input[@type="submit" and @name="submit"]')
                    submit_btn.click()
                    self.logger.info("Clicked submit button as fallback.")
                    time.sleep(2)
                    self.logger.info(f"Current URL after clicking submit: {self.driver.current_url}")
                except Exception as e2:
                    self.logger.error(f"Could not find or click submit button: {e2}. Current URL: {self.driver.current_url}")
                    return False
                
                # Wait again for redirect
                for i in range(20):
                    new_url = self.driver.current_url
                    if "cas.imt-atlantique.fr/cas/login" not in new_url:
                        self.logger.info(f"Left CAS login page after clicking submit, new URL: {new_url}")
                        break
                    time.sleep(0.5)
                else:
                    self.logger.error(f"Still on CAS login page after all attempts. Current URL: {self.driver.current_url}")
                    try:
                        msg_elem = self.driver.find_element(By.XPATH, '//*[@id="msg"]')
                        if msg_elem.is_displayed() and msg_elem.text.strip():
                            self.logger.error(f"Login error message displayed: {msg_elem.text.strip()}. Current URL: {self.driver.current_url}")
                    except NoSuchElementException:
                        self.logger.info("No login error message element found after all attempts (NoSuchElementException).")
                    except Exception:
                        self.logger.info("No login error message element found after all attempts.")
                    return False
            
            return True
        except Exception as e:
            self.logger.error(f"Error in step 2: {e}. Current URL: {self.driver.current_url if self.driver else 'driver not initialized'}")
            return False
    
    def step2b_handle_saml_post_sso(self):
        """
        Step 2b: Handle SAML POST SSO if present
        """
        try:
            current_url = self.driver.current_url
            if "https://idp.imt-atlantique.fr/idp/profile/SAML2/POST/SSO" in current_url:
                self.logger.info("SAML2 POST SSO detected, clicking accept button")
                try:
                    button = self.driver.find_element(By.XPATH, '/html/body/form/div/div[2]/p[2]/input[2]')
                    button.click()
                    self.logger.info("Clicked SAML2 SSO accept button")
                    time.sleep(2)
                    return True
                except Exception as e:
                    self.logger.error(f"Could not find or click SAML2 SSO button: {e}")
                    return False
            else:
                self.logger.info("No SAML2 POST SSO step needed")
                return True
        except Exception as e:
            self.logger.error(f"Error in step2b_handle_saml_post_sso: {e}")
            return False

    def step3_navigate_to_search(self):
        """
        Step 3: Navigate to Annuaire/Annuaires search page, go inside MANavigationBase frame, then MARecherche frame, and download its content.
        """
        try:
            self.logger.info("Step 3: Navigating directly to Annuaire/Annuaires search page")
            self.driver.get("https://pass.imt-atlantique.fr/OpDotNet/Noyau/Default.aspx?")
            time.sleep(4)
            
            # Wait for the page to load after login and for the correct URL
            for i in range(20):  # up to ~10 seconds
                current_url = self.driver.current_url
                if "https://pass.imt-atlantique.fr/OpDotNet/Noyau/Default.aspx?" in current_url:
                    break
                time.sleep(0.5)
            else:
                current_url = self.driver.current_url
                self.logger.error(f"Did not reach Default.aspx page after login. Last URL: {current_url}")
                return False
            
            # Use JS to set window.parent.content.location to Annuaire Accueil
            js = ("window.parent.content.location = '/OpDotNet/Eplug/Annuaire/Accueil.aspx?IdApplication=142&TypeAcces=Utilisateur&IdLien=242&groupe=31';")
            self.driver.execute_script(js)
            self.logger.info("Executed JS to set window.parent.content.location to Annuaire Accueil page.")

            try:
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame(3) # KEEP THE 3 HARD-CODED INDEX!!!!!!!
                self.logger.info("Switched to content frame (index 3)")

                # Switch to MANavigationBase frame
                try:
                    navigation_base_frame = WebDriverWait(self.driver, self.timeout).until(
                        EC.presence_of_element_located((By.NAME, "MANavigationBase"))
                    )
                    self.driver.switch_to.frame(navigation_base_frame)
                    self.logger.info("Switched to MANavigationBase frame")
                    # Log the HTML content of MANavigationBase frame for debugging
                    try:
                        navigation_base_html = self.driver.execute_script("return document.documentElement.outerHTML;")
                        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                        navigation_base_path = os.path.join('data', f'MANavigationBase_debug_{ts}.html')
                        with open(navigation_base_path, 'w', encoding='utf-8') as f:
                            f.write(navigation_base_html)
                        self.logger.info(f"Saved HTML of MANavigationBase frame to: {navigation_base_path}")
                    except Exception as e:
                        self.logger.error(f"Could not save HTML of MANavigationBase frame: {e}")
                    # Retry switching to MARecherche frame
                    for attempt in range(5):
                        try:
                            recherche_frame = WebDriverWait(self.driver, self.timeout).until(
                                EC.presence_of_element_located((By.NAME, "MARecherche"))
                            )
                            self.driver.switch_to.frame(recherche_frame)
                            self.logger.info("Switched to MARecherche frame")
                            # Retrieve the HTML content of MARecherche frame
                            try:
                                html = self.driver.execute_script("return document.documentElement.outerHTML;")
                                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                                html_path = os.path.join('data', f'MARecherche_debug_{ts}.html')
                                with open(html_path, 'w', encoding='utf-8') as f:
                                    f.write(html)
                                self.logger.info(f"Saved HTML of MARecherche frame to: {html_path}")
                                return True
                            except Exception as e:
                                self.logger.error(f"Could not retrieve HTML of MARecherche frame: {e}")
                                return False
                        except Exception as e:
                            self.logger.warning(f"Attempt {attempt + 1}: Could not switch to MARecherche frame: {e}")
                            time.sleep(1)  # Wait before retrying
                    self.logger.error("Failed to switch to MARecherche frame after multiple attempts")
                    return False
                except Exception as e:
                    self.logger.error(f"Could not switch to MANavigationBase frame: {e}")
                    return False
            except Exception as e:
                self.logger.error(f"Error switching frames in step 3: {e}. Current URL: {self.driver.current_url if self.driver else 'driver not initialized'}")
                return False
        except Exception as e:
            self.logger.error(f"Error in step 3 (outer): {e}. Current URL: {self.driver.current_url if self.driver else 'driver not initialized'}")
            return False

    def step4_search_person(self, first_name, last_name):
        """
        Step 4: Enter name and surname in search fields (Annuaire)
        
        Args:
            first_name (str): First name to search
            last_name (str): Last name to search
        """
        try:
            self.logger.info("Step 4: Entering search criteria (Annuaire)")

            # Enter search criteria directly
            full_name = f"{first_name} {last_name}"
            search_input_xpath = '//*[@id="txtRecherche"]'
            search_button_xpath = '//*[@id="btnRecherche"]'

            try:
                search_input = WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.XPATH, search_input_xpath))
                )
                search_input.clear()
                search_input.send_keys(full_name)
                self.logger.info(f"Filled search field with: {full_name}")
            except Exception as e:
                self.logger.error(f"Could not find or fill search field: {e}. Current URL: {self.driver.current_url}")
                return False

            # Click the search button
            try:
                search_button = WebDriverWait(self.driver, self.timeout).until(
                    EC.element_to_be_clickable((By.XPATH, search_button_xpath))
                )
                search_button.click()
                self.logger.info("Clicked search button")
            except Exception as e:
                self.logger.error(f"Could not find or click search button: {e}. Current URL: {self.driver.current_url}")
                return False

            time.sleep(2)  # Wait for results to load
            return True
        except Exception as e:
            self.logger.error(f"Error in step 4: {e}. Current URL: {self.driver.current_url if self.driver else 'driver not initialized'}")
            return False
    
    def step5_get_result_link(self, first_name, last_name, user_id):
        """
        Step 5: Get specific link from search results (Annuaire) and cache user's pass ID in the database.

        Args:
            first_name (str): First name of the user
            last_name (str): Last name of the user

        Returns:
            str: URL of the result link or None if not found
        """
        try:
            self.logger.info("Step 5: Switching to MAContenu frame to retrieve search results")

            # Switch out of MARecherche frame
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame(3)  # Content frame
            self.driver.switch_to.frame("MANavigationBase")

            # Switch to MAContenu frame
            try:
                contenu_frame = WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.NAME, "MAContenu"))
                )
                self.driver.switch_to.frame(contenu_frame)
                self.logger.info("Switched to MAContenu frame")

                # Save the HTML content of MAContenu frame for debugging
                try:
                    contenu_html = self.driver.execute_script("return document.documentElement.outerHTML;")
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    contenu_path = os.path.join('data', f'MAContenu_debug_{ts}.html')
                    with open(contenu_path, 'w', encoding='utf-8') as f:
                        f.write(contenu_html)
                    self.logger.info(f"Saved HTML of MAContenu frame to: {contenu_path}")
                except Exception as e:
                    self.logger.error(f"Could not save HTML of MAContenu frame: {e}")

                # Try to find the user id by scanning all <a> with ouvrirDossierObjet in onclick
                try:
                    links = self.driver.find_elements(By.XPATH, "//a[contains(@onclick, 'ouvrirDossierObjet(')]")
                    for link in links:
                        onclick_attr = link.get_attribute('onclick')
                        match = re.search(r"ouvrirDossierObjet\((\d+),", onclick_attr)
                        if not match:
                            continue
                        # Check for a sibling mailto link with the right email
                        parent_td = link.find_element(By.XPATH, './ancestor::td[1]')
                        try:
                            sibling_email_link = parent_td.find_element(By.XPATH, "following-sibling::td//a[starts-with(@href, 'mailto:')]")
                            email_text = sibling_email_link.text.strip().lower()
                            
                            if first_name.lower() in email_text or last_name.lower() in email_text:
                                object_id = match.group(1)
                                profile_url = f"https://pass.imt-atlantique.fr/OpDotNet/eplug/Annuaire/Navigation/Dossier/Dossier.aspx?IdObjet={object_id}&IdTypeObjet=25&IdAnn=&IdProfil=&AccesPerso=false&Wizard="
                                self.logger.info(f"Found profile URL: {profile_url}")

                                # Step 5b: Cache user's pass ID in the database
                                self.step5b_cache_pass_id(int(user_id), int(object_id))

                                return profile_url
                        except Exception:
                            # If no email, fallback to check if the link text matches first or last name
                            link_text = link.text.strip().lower()
                            if first_name.lower() in link_text or last_name.lower() in link_text:
                                object_id = match.group(1)
                                profile_url = f"https://pass.imt-atlantique.fr/OpDotNet/eplug/Annuaire/Navigation/Dossier/Dossier.aspx?IdObjet={object_id}&IdTypeObjet=25&IdAnn=&IdProfil=&AccesPerso=false&Wizard="
                                self.logger.info(f"Found profile URL (fallback): {profile_url}")

                                # Step 5b: Cache user's pass ID in the database
                                self.step5b_cache_pass_id(int(user_id), int(object_id))

                                return profile_url
                    self.logger.error(f"No user link found for {first_name} {last_name} in MAContenu.")
                    return None
                except Exception as e:
                    self.logger.error(f"Error finding user link: {e}")
                    return None
            except Exception as e:
                self.logger.error(f"Could not switch to MAContenu frame: {e}")
                return None
        except Exception as e:
            self.logger.error(f"Error in step 5: {e}")
            return None

    def step5b_cache_pass_id(self, user_id: int, pass_id: int):
        """
        Step 5b: Cache user's pass ID in the database via an API PATCH request.

        Args:
            user_id (int): The user ID
            pass_id (int): The pass ID to cache
        """
        api_client = ApiClient()

        # Ensure the client is authenticated.
        if not api_client.token:
            try:
                email = Config.TRANSAT_API_EMAIL
                password = Config.TRANSAT_API_PASSWORD
                api_client.authenticate(email, password)
            except requests.exceptions.ConnectionError as e:
                self.logger.error(f"API connection error: {e}. Is the API server running at {api_client.base_api_url}?")
                return {'error': f'API connection error: {e}. Is the API server running at {api_client.base_api_url}?'}
            except Exception as e:
                self.logger.error(f"API authentication failed: {e}")
                return {'error': f'API authentication failed: {e}'}

        # Attempt to patch pass ID.
        try:
            api_client.patch_user_pass_id(user_id, pass_id)
            self.logger.info(f"Successfully cached pass ID {pass_id} in the database.")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to cache pass ID {pass_id}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error in step5b_cache_pass_id: {e}")


    def step6_scrape_data(self, result_url):
        try:
            self.logger.info("Step 6: Navigating to result page and scraping data")
            self.driver.get(result_url)
            time.sleep(3)

            if "Dossier.aspx?IdObjet=" not in self.driver.current_url:
                return {'error': f'Unexpected URL: {self.driver.current_url}', 'url': self.driver.current_url}

            WebDriverWait(self.driver, self.timeout).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "frm0")))

            # Extract month and year from the header
            header_text = self.driver.find_element(
                By.XPATH, "//td[@class='AuthentificationMenu' and contains(text(),'Agenda de l')]"
            ).text
            month_year_match = re.search(r'([A-Za-zéû]+)\s+(\d{4})$', header_text.strip())
            if not month_year_match:
                raise Exception("Could not extract month and year from planning header.")
            french_month, year = month_year_match.groups()
            month_map = {
                "Janvier": 1, "Février": 2, "Mars": 3, "Avril": 4,
                "Mai": 5, "Juin": 6, "Juillet": 7, "Août": 8,
                "Septembre": 9, "Octobre": 10, "Novembre": 11, "Décembre": 12
            }
            month = month_map.get(french_month)
            if not month:
                raise Exception(f"Unrecognized French month name: {french_month}")

            # Extract column headers (day name + day number)
            header_cells = self.driver.find_elements(By.XPATH, "//tr[contains(@class,'fondTresClair')]/td[position()>1]")
            days = []
            for i, cell in enumerate(header_cells):
                text = cell.text.strip()
                match = re.match(r"(\w+)\s+(\d{2})", text)
                if match:
                    day_name, day_num = match.groups()
                    full_date = datetime(int(year), month, int(day_num)).strftime("%Y-%m-%d")
                    days.append((day_name, full_date))
                else:
                    days.append((f"Day{i}", None))  # fallback if missing

            planning = []

            # Traverse planning rows
            rows = self.driver.find_elements(By.XPATH, "//tr[td[@bgcolor='#DDDDDD']]")
            for row in rows:
                try:
                    cells = row.find_elements(By.XPATH, "./td")
                    if len(cells) < 8:
                        continue
                    time_slot = cells[0].text.strip()

                    for i, (day_name, date_str) in enumerate(days):
                        container_cells = cells[i + 1].find_elements(By.XPATH, ".//td[@class='GEDcellsouscategorie']")
                        for course_cell in container_cells:
                            try:
                                title = course_cell.find_element(By.TAG_NAME, 'b').text.strip()
                                font_elements = course_cell.find_elements(By.TAG_NAME, 'font')
                                start_time = end_time = teacher = room = group = ""
                                values = [e.text.strip() for e in font_elements]

                                if values and '-' in values[0]:
                                    start_time, end_time = map(str.strip, values[0].split('-'))

                                for val in values[1:]:
                                    if re.search(r"\bFISE|FIT|FIL|PROMO|GPE|ANNÉE\b", val, re.IGNORECASE):
                                        group = val
                                    elif re.match(r"^[A-Z]{2}-[A-Z0-9]+", val) or '(' in val:
                                        room = val
                                    elif re.match(r"[A-Z][a-z]+ [A-Z][a-z]+", val):
                                        teacher = val

                                planning.append({
                                    'date': date_str,
                                    'title': title,
                                    'start_time': start_time,
                                    'end_time': end_time,
                                    'teacher': teacher,
                                    'room': room,
                                    'group': group
                                })

                            except Exception as e:
                                self.logger.warning(f"Failed to parse course cell at {date_str} {time_slot}: {e}")
                except Exception as e:
                    self.logger.warning(f"Failed to parse row: {e}")

            return {
                'url': result_url,
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'planning': planning
            }

        except Exception as e:
            self.logger.error(f"Error in step 6: {e}")
            return {'error': str(e)}
    
    def step8_send_courses_to_api(self, planning, TEMPORARY_USER_EMAIL, transat_api_email, transat_api_password):
        """
        Step 8: Send each course in planning to the API
        Args:
            planning (list): List of course dicts
            TEMPORARY_USER_EMAIL (str): Email of the user whose planning it is
            transat_api_email (str): Email for API authentication
            transat_api_password (str): Password for API authentication
        """
        client = ApiClient()
        try:
            client.authenticate(transat_api_email, transat_api_password)
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"API connection error: {e}. Is the API server running at {client.base_api_url}?")
            return {'error': f'API connection error: {e}. Is the API server running at {client.base_api_url}?'}
        except Exception as e:
            self.logger.error(f"API authentication failed: {e}")
            return {'error': f'API authentication failed: {e}'}
        success_count = 0
        for course in planning:
            course_payload = course.copy()
            course_payload["TEMPORARY_USER_EMAIL"] = TEMPORARY_USER_EMAIL
            try:
                client.post_course(course_payload)
                success_count += 1
            except Exception as e:
                self.logger.error(f"Failed to send course to API: {course_payload} | Error: {e}")
        self.logger.info(f"Step 8: Sent {success_count}/{len(planning)} courses to API.")
        return success_count == len(planning)
    
    def run_full_scrape(self, username, password):
        """
        Run the complete scraping flow
        
        Args:
            username (str): Login username
            password (str): Login password
            
        Returns:
            dict: Scraped data or error information
        """
        try:
            self.logger.info("Starting complete scraping flow")
            
            # Step 0: Authenticate to API before starting scraping.
            TRANSAT_API_EMAIL = Config.TRANSAT_API_EMAIL
            TRANSAT_API_PASSWORD = Config.TRANSAT_API_PASSWORD

            client = ApiClient()
            try:
                client.authenticate(TRANSAT_API_EMAIL, TRANSAT_API_PASSWORD)
            except requests.exceptions.ConnectionError as e:
                self.logger.error(f"API connection error: {e}. Is the API server running at {client.base_api_url}?")
                return {'error': f'API connection error: {e}. Is the API server running at {client.base_api_url}?'}
            except Exception as e:
                self.logger.error(f"API authentication failed: {e}")
                return {'error': f'API authentication failed: {e}'}
            
            # Step 1: Select authentication mode
            if not self.step1_select_auth_mode():
                return {'error': 'Failed at step 1: Auth mode selection'}
            
            # Step 2: Login
            if not self.step2_login(username, password):
                return {'error': 'Failed at step 2: Login'}
            
            # Step 2b: Handle SAML POST SSO if present
            if not self.step2b_handle_saml_post_sso():
                return {'error': 'Failed at step 2b: SAML POST SSO'}
            
            # Step 3: Navigate to search page
            if not self.step3_navigate_to_search():
                return {'error': 'Failed at step 3: Navigation'}
            
            # # Step 4: Search for person
            if not self.step4_search_person("chavanel", "yohann"):
                 return {'error': 'Failed at step 4: Search'}
            
            # Step 5: Get result link
            result_url = self.step5_get_result_link("chavanel", "yohann", Config.TEMPORARY_USER_ID)
            if not result_url:
                 return {'error': 'Failed at step 5: No result link found'}
            
            # Step 6: Scrape data
            scraped_data = self.step6_scrape_data(result_url)
            
            # Step 7: (optional) Any post-processing here

            # Step 8: Send courses to API
            if 'planning' in scraped_data and scraped_data['planning']:
                self.step8_send_courses_to_api(scraped_data['planning'], Config.TEMPORARY_USER_EMAIL, TRANSAT_API_EMAIL, TRANSAT_API_PASSWORD)
            
            self.logger.info("Complete scraping flow finished successfully")
            return scraped_data
        except Exception as e:
            self.logger.error(f"Error in complete scraping flow: {e}")
            return {'error': f'Complete flow failed: {str(e)}'}
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            self.logger.info("Browser closed")