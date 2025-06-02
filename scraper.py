from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import time
import logging

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
            except Exception as e:
                self.logger.info(f"No login error message element found after submit. Current URL: {self.driver.current_url}. Exception: {e}")
            
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
                    except Exception as e:
                        self.logger.info(f"No login error message element found after all attempts. Exception: {e}")
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

    def step3_navigate_to_search(self, navigation_button_selector=None):
        """
        Step 3: Navigate to specific page by clicking a button
        
        Args:
            navigation_button_selector (str): CSS selector or XPath for the navigation button
        """
        try:
            self.logger.info("Step 3: Navigating to search page")
            
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
            self.logger.info(f"On Default.aspx page ({self.driver.current_url}), proceeding to click Annuaire/Annuaires button")
            # Try to click the Annuaire/Annuaires button by XPath for <a id="242">
            try:
                annuaire_btn = self.driver.find_element(By.XPATH, '//a[@id="242"]')
                self.driver.execute_script("arguments[0].click();", annuaire_btn)
                self.logger.info("Clicked Annuaire/Annuaires button by XPath and JS click.")
                time.sleep(2)
                return True
            except Exception as e:
                self.logger.error(f"Could not click Annuaire/Annuaires button: {e}. Current URL: {self.driver.current_url}")
                # As fallback, try to directly navigate to the Annuaire page if possible
                try:
                    self.logger.info("Trying direct navigation to Annuaire/Annuaires page as fallback.")
                    self.driver.get("https://pass.imt-atlantique.fr/OpDotNet/Eplug/Annuaire/Accueil.aspx?IdApplication=142&TypeAcces=Utilisateur&IdLien=242&groupe=31")
                    time.sleep(2)
                    return True
                except Exception as e2:
                    self.logger.error(f"Direct navigation to Annuaire page failed: {e2}. Current URL: {self.driver.current_url}")
                    return False
        except Exception as e:
            self.logger.error(f"Error in step 3: {e}. Current URL: {self.driver.current_url if self.driver else 'driver not initialized'}")
            return False
    
    def step4_search_person(self, first_name, last_name):
        """
        Step 4: Enter name and surname in search fields
        
        Args:
            first_name (str): First name to search
            last_name (str): Last name to search
        """
        try:
            self.logger.info("Step 4: Entering search criteria")
            
            # Common field selectors for name search
            first_name_selectors = [
                "input[name*='first']",
                "input[name*='prenom']",
                "input[name*='fname']",
                "input[id*='first']",
                "input[id*='prenom']",
                "#firstName",
                "#prenom"
            ]
            
            last_name_selectors = [
                "input[name*='last']",
                "input[name*='nom']",
                "input[name*='lname']",
                "input[id*='last']",
                "input[id*='nom']",
                "#lastName",
                "#nom"
            ]
            
            # Try to fill first name
            first_name_filled = False
            for selector in first_name_selectors:
                try:
                    if self.wait_and_send_keys(By.CSS_SELECTOR, selector, first_name):
                        first_name_filled = True
                        break
                except:
                    continue
            
            # Try to fill last name
            last_name_filled = False
            for selector in last_name_selectors:
                try:
                    if self.wait_and_send_keys(By.CSS_SELECTOR, selector, last_name):
                        last_name_filled = True
                        break
                except:
                    continue
            
            # If we couldn't find separate fields, try a single search field
            if not (first_name_filled and last_name_filled):
                single_search_selectors = [
                    "input[type='search']",
                    "input[name*='search']",
                    "input[name*='query']",
                    "#search",
                    ".search-input"
                ]
                
                full_name = f"{first_name} {last_name}"
                for selector in single_search_selectors:
                    try:
                        if self.wait_and_send_keys(By.CSS_SELECTOR, selector, full_name):
                            self.logger.info("Filled single search field")
                            break
                    except:
                        continue
            
            # Click search button
            search_button_selectors = [
                "input[type='submit']",
                "button[type='submit']",
                "input[value*='Search']",
                "button:contains('Search')",
                "input[value*='Recherch']",
                "button:contains('Recherch')",
                "#search-button",
                ".search-button"
            ]
            
            search_clicked = False
            for selector in search_button_selectors:
                try:
                    if self.wait_and_click(By.CSS_SELECTOR, selector):
                        search_clicked = True
                        self.logger.info("Search initiated")
                        break
                except:
                    continue
            
            if not search_clicked:
                self.logger.warning("Could not find search button")
            
            time.sleep(3)  # Wait for search results
            return True
            
        except Exception as e:
            self.logger.error(f"Error in step 4: {e}")
            return False
    
    def step5_get_result_link(self):
        """
        Step 5: Get specific link from search results
        
        Returns:
            str: URL of the result link or None if not found
        """
        try:
            self.logger.info("Step 5: Getting result link from search results")
            
            # Wait for results to load
            time.sleep(3)
            
            # Common selectors for result links
            result_link_selectors = [
                "a[href*='detail']",
                "a[href*='profile']",
                "a[href*='person']",
                ".result-link",
                ".person-link",
                "tbody tr td a",
                ".search-result a"
            ]
            
            for selector in result_link_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        link_url = elements[0].get_attribute('href')
                        if link_url:
                            self.logger.info(f"Found result link: {link_url}")
                            return link_url
                except:
                    continue
            
            # Try XPath selectors
            xpath_selectors = [
                "//a[contains(@href, 'detail')]",
                "//a[contains(@href, 'profile')]",
                "//tr/td/a",
                "//div[@class='result']//a"
            ]
            
            for xpath in xpath_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    if elements:
                        link_url = elements[0].get_attribute('href')
                        if link_url:
                            self.logger.info(f"Found result link via XPath: {link_url}")
                            return link_url
                except:
                    continue
            
            self.logger.error("Could not find result link")
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
    
    def run_full_scrape(self, username, password, navigation_button_selector=None):
        """
        Run the complete scraping flow
        
        Args:
            username (str): Login username
            password (str): Login password
            first_name (str): First name to search
            last_name (str): Last name to search
            navigation_button_selector (str): Optional selector for navigation button
            
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
            if not self.step3_navigate_to_search(navigation_button_selector):
                return {'error': 'Failed at step 3: Navigation'}
            
            # # Step 4: Search for person
            # if not self.step4_search_person(first_name, last_name):
            #     return {'error': 'Failed at step 4: Search'}
            
            # # Step 5: Get result link
            # result_url = self.step5_get_result_link()
            # if not result_url:
            #     return {'error': 'Failed at step 5: No result link found'}
            
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