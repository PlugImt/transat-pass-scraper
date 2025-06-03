from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import time
import logging
from datetime import datetime
import os
import re
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
    
    def step5_get_result_link(self, first_name, last_name):
        """
        Step 5: Get specific link from search results (Annuaire)

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
                                return profile_url
                        except Exception:
                            # If no email, fallback to check if the link text matches first or last name
                            link_text = link.text.strip().lower()
                            if first_name.lower() in link_text or last_name.lower() in link_text:
                                object_id = match.group(1)
                                profile_url = f"https://pass.imt-atlantique.fr/OpDotNet/eplug/Annuaire/Navigation/Dossier/Dossier.aspx?IdObjet={object_id}&IdTypeObjet=25&IdAnn=&IdProfil=&AccesPerso=false&Wizard="
                                self.logger.info(f"Found profile URL (fallback): {profile_url}")
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
    
    def step6_scrape_data(self, result_url):
        """
        Step 6: Navigate to result link and scrape data
        
        Args:
            result_url (str): URL to scrape data from
            
        Returns:
            dict: Scraped data
        """
        try:
            self.logger.info("Step 6: Navigating to result page and scraping data")
            
            # Navigate to the result URL
            self.driver.get(result_url)
            time.sleep(3)
            
            # Initialize data dictionary
            scraped_data = {
                'url': result_url,
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Common data fields to scrape
            data_selectors = {
                'name': ['h1', '.name', '#name', '.person-name'],
                'email': ['a[href^="mailto:"]', '.email', '#email'],
                'phone': ['.phone', '#phone', '.telephone'],
                'department': ['.department', '#department', '.service'],
                'position': ['.position', '#position', '.title', '.poste'],
                'office': ['.office', '#office', '.bureau'],
                'address': ['.address', '#address', '.adresse']
            }
            
            # Scrape each type of data
            for field, selectors in data_selectors.items():
                for selector in selectors:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if element and element.text.strip():
                            if field == 'email' and element.get_attribute('href'):
                                scraped_data[field] = element.get_attribute('href').replace('mailto:', '')
                            else:
                                scraped_data[field] = element.text.strip()
                            break
                    except:
                        continue
            
            # Scrape all text content as fallback
            try:
                body_text = self.driver.find_element(By.TAG_NAME, 'body').text
                scraped_data['full_text'] = body_text
            except:
                pass
            
            # Scrape all links
            try:
                links = []
                link_elements = self.driver.find_elements(By.TAG_NAME, 'a')
                for link in link_elements:
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    if href and text:
                        links.append({'url': href, 'text': text})
                scraped_data['links'] = links
            except:
                pass
            
            self.logger.info(f"Successfully scraped data: {len(scraped_data)} fields")
            return scraped_data
            
        except Exception as e:
            self.logger.error(f"Error in step 6: {e}")
            return {'error': str(e), 'url': result_url}
    
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
            result_url = self.step5_get_result_link("chavanel", "yohann")
            if not result_url:
                 return {'error': 'Failed at step 5: No result link found'}
            
            # # Step 6: Scrape data
            # scraped_data = self.step6_scrape_data(result_url)
            
            self.logger.info("Complete scraping flow finished successfully")
            # return scraped_data
        except Exception as e:
            self.logger.error(f"Error in complete scraping flow: {e}")
            return {'error': f'Complete flow failed: {str(e)}'}
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            self.logger.info("Browser closed")