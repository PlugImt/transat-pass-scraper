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
from datetime import datetime
from steps.step7_optimize_planning import step7_optimize_planning

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
            self.logger.info(f"Step 6: Navigating to user planning page {result_url}")
            self.driver.get(result_url)
            time.sleep(3)

            if "Dossier.aspx?IdObjet=" not in self.driver.current_url:
                return {'error': f'Unexpected URL: {self.driver.current_url}', 'url': self.driver.current_url}

            self.logger.info("On user planning page. Looking for 'Agenda' tab.")
            self.driver.switch_to.default_content()

            # XPath to find the tab containing the text "Agenda" and click it.
            agenda_tab_xpath = "//nobr[text()='Agenda']/ancestor::table[contains(@onclick, 'ComponentArt_TabStrip_TabClick')]"
            try:
                agenda_tab = WebDriverWait(self.driver, self.timeout).until(
                    EC.element_to_be_clickable((By.XPATH, agenda_tab_xpath))
                )
                agenda_tab.click()
                self.logger.info("Clicked the 'Agenda' tab.")
                time.sleep(3) # Wait for the iframe content to start loading.
            except TimeoutException:
                self.logger.error("Could not find or click the 'Agenda' tab.")
                return {'error': "Could not find or click the 'Agenda' tab."}

            # Now, wait for the correct iframe for the agenda (frm1) and switch to it.
            self.logger.info("Waiting for the agenda content to load in iframe 'frm1'...")
            WebDriverWait(self.driver, self.timeout).until(
                EC.frame_to_be_available_and_switch_to_it((By.ID, "frm1"))
            )
            self.logger.info("Switched to iframe 'frm1'.")

            # Wait for a specific element inside the iframe to confirm the planning has loaded.
            planning_header_xpath = "//td[@class='AuthentificationMenu' and contains(text(),'Agenda de l')]"
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.XPATH, planning_header_xpath))
            )
            self.logger.info("Agenda planning table is visible. Starting to scrape.")

            # Extract month and year from the header.
            header_text = self.driver.find_element(By.XPATH, planning_header_xpath).text
            month_year_match = re.search(r'([A-Za-zéû]+)\s+(\d{4})$', header_text.strip())
            if not month_year_match:
                # If scraping fails here, it might be because the page is still loading.
                # A screenshot could be helpful for debugging.
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                self.driver.save_screenshot(os.path.join('data', f'scrape_fail_{ts}.png'))
                raise Exception("Could not extract month and year from planning header.")
            
            french_month, year = month_year_match.groups()
            month_map = {
                "Janvier": 1, "Février": 2, "Mars": 3, "Avril": 4, "Mai": 5, "Juin": 6, 
                "Juillet": 7, "Août": 8, "Septembre": 9, "Octobre": 10, "Novembre": 11, "Décembre": 12
            }
            month = month_map.get(french_month)

            if not month:
                raise Exception(f"Unrecognized French month name: {french_month}")

            header_cells = self.driver.find_elements(By.XPATH, "//tr[contains(@class,'fondTresClair')]/td[position()>1]")
            days = []
            for i, cell in enumerate(header_cells):
                text = cell.text.strip().replace('\xa0', ' ')
                match = re.match(r"(\w+)\s+(\d{1,2})", text)
                if match:
                    day_name, day_num = match.groups()
                    full_date = datetime(int(year), month, int(day_num)).strftime("%Y-%m-%d")
                    days.append((day_name, full_date))
                else:
                    days.append((f"Day{i}", None))

            self.logger.info(f"Detected days for scraping are {days}.")

            planning = []

            # Traverse planning rows
            rows = self.driver.find_elements(By.XPATH, "//tr[td[@bgcolor='#DDDDDD']]")
            self.logger.info(f"Found {len(rows)} rows to process.")
            
            for row in rows:
                try:
                    cells = row.find_elements(By.XPATH, "./td")
                    if len(cells) < len(days) + 1:
                        continue

                    for i, (day_name, date_str) in enumerate(days):
                        if date_str is None: continue
                        
                        course_cell = cells[i + 1]
                        
                        bgcolor = course_cell.get_attribute('bgcolor')
                        if not bgcolor or bgcolor.lower() == '#ededed':
                            continue
                        
                        try:
                            # Check for the bold tag to confirm it's a course title cell.
                            title_element = course_cell.find_element(By.TAG_NAME, 'b')
                            title = title_element.text.strip().replace(' ', ' ')

                            all_text_parts = course_cell.text.split('\n')
                            
                            start_time_obj, end_time_obj = None, None
                            teachers = []
                            room, group = "", ""

                            for part in all_text_parts:
                                time_match = re.search(r'(\d{2})H(\d{2})-(\d{2})H(\d{2})', part)
                                if time_match:
                                    start_h, start_m, end_h, end_m = time_match.groups()
                                    start_time_obj = datetime.strptime(f"{date_str} {start_h}:{start_m}", "%Y-%m-%d %H:%M")
                                    end_time_obj = datetime.strptime(f"{date_str} {end_h}:{end_m}", "%Y-%m-%d %H:%M")
                                    continue
                                
                                if re.search(r"\bFISE|FIT|FIL|PROMO|GPE|ANNÉE|LV1|DEMI\b", part, re.IGNORECASE):
                                    group = part
                                    continue
                                
                                if re.match(r"^[A-Z]{2,}-.*", part) or '(' in part:
                                    room = part
                                    continue

                                # Match names, but exclude the title itself.
                                if part != title and re.fullmatch(r"[A-Z'’\s-]+ [A-Z][a-z'’-]+", part, re.IGNORECASE):
                                    teachers.append(part)

                            planning.append({
                                'date': date_str,
                                'title': title,
                                'start_time': start_time_obj,
                                'end_time': end_time_obj,
                                'teacher': ", ".join(teachers),
                                'room': room,
                                'group': group
                            })

                        except NoSuchElementException:
                            # This cell has a color but no <b> tag, so it's likely a continued event (due to rowspan). Skip it.
                            continue
                        except Exception as e:
                            self.logger.warning(f"Error parsing course cell on {date_str}: {e}")
                except Exception as e:
                    self.logger.warning(f"Failed to parse row: {e}")

            # Remove duplicate course in list.
            unique_planning = []
            seen = set()
            for d in planning:
                # Create a tuple of the course's identifying info.
                course_tuple = (d['date'], d['title'], d['teacher'], d['room'], d['group'], d['start_time'])

                if course_tuple not in seen:
                    unique_planning.append(d)
                    seen.add(course_tuple)
            
            self.logger.info(f"Found and parsed {len(unique_planning)} unique course entries.")

            return {
                'url': result_url,
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'planning': unique_planning
            }

        except Exception as e:
            self.logger.error(f"CRITICAL ERROR in step 6: {e}", exc_info=True)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            error_screenshot_path = os.path.join('data', f'step6_error_{ts}.png')
            try:
                self.driver.save_screenshot(error_screenshot_path)
                self.logger.info(f"Saved error screenshot to {error_screenshot_path}")
            except Exception as e_ss:
                self.logger.error(f"Could not save error screenshot: {e_ss}")

            return {'error': str(e)}
        
    def step8_send_courses_to_api(self, planning, user_id, transat_api_email, transat_api_password):
        """
        Step 8: Send each course in planning to the API
        Args:
            planning (list): List of course dicts
            user_id (int): ID of the user whose planning it is
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
            course_payload["user_id"] = user_id
            try:
                client.post_course(course_payload)
                success_count += 1
            except Exception as e:
                self.logger.error(f"Failed to send course to API: {course_payload} | Error: {e}")
        self.logger.info(f"Step 8: Sent {success_count}/{len(planning)} courses to API for user {user_id}.")
        return success_count == len(planning)

    def run_full_scrape(self, pass_username, pass_password):
        """
        Run the complete scraping flow for all users from the API.
        
        Args:
            pass_username (str): Login username for the PASS account.
            pass_password (str): Login password for the PASS account.
            
        Returns:
            dict: A summary of the scraping process including all plannings.
        """
        try:
            self.logger.info("Starting complete scraping flow for all users!")
            
            # Step 0: Authenticate to API before starting scraping.
            TRANSAT_API_EMAIL = Config.TRANSAT_API_EMAIL
            TRANSAT_API_PASSWORD = Config.TRANSAT_API_PASSWORD

            client = ApiClient()
            try:
                client.authenticate(TRANSAT_API_EMAIL, TRANSAT_API_PASSWORD)
                self.logger.info("Successfully authenticated with the API.")
            except requests.exceptions.ConnectionError as e:
                self.logger.error(f"API connection error: {e}. Is the API server running at {client.base_api_url}?")
                return {'error': f'API connection error: {e}. Is the API server running at {client.base_api_url}?'}
            except Exception as e:
                self.logger.error(f"API authentication failed: {e}")
                return {'error': f'API authentication failed: {e}'}
            
            # Step 1: Select authentication mode.
            if not self.step1_select_auth_mode():
                return {'error': 'Failed at step 1: Auth mode selection'}
            
            # Step 2: Login.
            if not self.step2_login(pass_username, pass_password):
                return {'error': 'Failed at step 2: Login'}
            
            # Step 2b: Handle SAML POST SSO if present
            if not self.step2b_handle_saml_post_sso():
                return {'error': 'Failed at step 2b: SAML POST SSO'}

            # Get all users from the API.
            try:
                all_users = client.get_all_users()
                self.logger.info(f"Retrieved {len(all_users)} users from the API.")
            except Exception as e:
                self.logger.error(f"Failed to get users from API: {e}")
                return {'error': f"Failed to get users from API: {e}"}

            # Initialize results with a dictionary to hold all plannings, keyed by pass_id.
            results = {
                'processed': 0, 
                'success': 0, 
                'failed': 0, 
                'failures': [], 
                'all_plannings': {}
            }

            # Loop through each user.
            for user in all_users:
                user_id = user.get('id')
                first_name = user.get('first_name', '').strip()
                last_name = user.get('last_name', '').strip()
                cached_pass_id = user.get('pass_id')
                
                results['processed'] += 1
                self.logger.info(f"--- Processing user #{user_id}: {first_name} {last_name} ---")

                try:
                    result_url = None
                    # Check if pass_id is cached.
                    if cached_pass_id:
                        self.logger.info(f"User has a cached pass_id: {cached_pass_id}. Skipping search.")
                        result_url = f"https://pass.imt-atlantique.fr/OpDotNet/eplug/Annuaire/Navigation/Dossier/Dossier.aspx?IdObjet={cached_pass_id}&IdTypeObjet=25&IdAnn=&IdProfil=&AccesPerso=false&Wizard="
                    else:
                        self.logger.info("User has no pass_id. Searching for user...")
                        
                        # Step 3: Navigate to search page.
                        if not self.step3_navigate_to_search():
                            raise Exception('Failed at step 3: Navigation')
                        
                        # Step 4: Search for person.
                        if not self.step4_search_person(first_name, last_name):
                            raise Exception(f'Failed at step 4: Search for {first_name} {last_name}')
                        
                        # Step 5: Get result link (and cache pass_id)
                        result_url = self.step5_get_result_link(first_name, last_name, user_id)
                        if not result_url:
                            raise Exception(f'Failed at step 5: No result link found for {first_name} {last_name}')

                    # Step 6: Scrape data.
                    scraped_data = self.step6_scrape_data(result_url)
                    if 'error' in scraped_data:
                        raise Exception(f"Failed at step 6: Scraping data. Error: {scraped_data['error']}")
                    
                    # print(scraped_data)

                    # Step 7: Optimize scraped data by merging consecutive courses.
                    if 'planning' in scraped_data and scraped_data['planning']:
                        self.logger.info(f"Step 7: Optimizing planning for user {user_id}.")
                        optimized_planning = step7_optimize_planning(scraped_data['planning'])
                        scraped_data['planning'] = optimized_planning
                    else:
                        self.logger.info(f"Step 7: No planning data to optimize for user {user_id}.")

                    """# Step 8: Send courses to API
                    if 'planning' in scraped_data and scraped_data['planning']:
                        if not self.step8_send_courses_to_api(scraped_data['planning'], user_id, TRANSAT_API_EMAIL, TRANSAT_API_PASSWORD):
                           self.logger.warning(f"Step 8: Not all courses were sent to API for user {user_id}.")
                        else:
                           self.logger.info(f"Step 8: Successfully sent all courses for user {user_id} to API.")
                    else:
                        self.logger.info(f"No planning data found for user {user_id} to send to API.") """

                    # Store the scraped data in the `all_plannings` dict using pass_id as the key.
                    results['all_plannings'][user_id] = scraped_data
                    results['success'] += 1
                    self.logger.info(f"--- Successfully processed user #{user_id} ---")

                except Exception as e:
                    self.logger.error(f"!!! Failed to process user #{user_id}: {first_name} {last_name}. Error: {e} !!!")
                    results['failed'] += 1
                    results['failures'].append({'user_id': user_id, 'name': f"{first_name} {last_name}", 'error': str(e)})
                    # Continue to the next user in the loop.
                    continue

            self.logger.info("Complete scraping flow for all users finished.")
            self.logger.info(f"Summary: {results}")
            return results
        except Exception as e:
            self.logger.error(f"Error in complete scraping flow: {e}", exc_info=True)
            return {'error': f'Complete flow failed: {str(e)}'}
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            self.logger.info("Browser closed")