import os
import time
import threading
import requests
from bs4 import BeautifulSoup
import customtkinter as ctk
from tkinter import filedialog, messagebox

# Set UI Theme and Color style
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class RedditToggleScraperApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("Reddit Image Downloader (All Filters Upgraded)")
        self.geometry("550x600")
        self.resizable(False, False)

        # Default Save Directory
        self.download_directory = os.path.join(os.path.expanduser("~"), "Downloads", "RedditDownloads")
        
        self.setup_ui()
        self.handle_toggle_switch() # Synchronize interface fields initial states

    def setup_ui(self):
        """Creates and positions all UI widgets."""
        # --- Title ---
        self.title_label = ctk.CTkLabel(self, text="Reddit Image Downloader", font=ctk.CTkFont(size=22, weight="bold"))
        self.title_label.pack(pady=(20, 15))

        # --- Subreddit URL Input Frame ---
        self.sub_frame = ctk.CTkFrame(self)
        self.sub_frame.pack(fill="x", padx=30, pady=5)
        
        self.sub_label = ctk.CTkLabel(self.sub_frame, text="Reddit Community URL:", font=ctk.CTkFont(size=13))
        self.sub_label.pack(side="left", padx=10, pady=10)
        
        self.sub_entry = ctk.CTkEntry(self.sub_frame, placeholder_text="Paste full https://www.reddit.com/r/... URL here", width=250)
        self.sub_entry.pack(side="right", padx=10, pady=10, expand=True, fill="x")

        # --- Toggle Switch Frame ---
        self.toggle_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.toggle_frame.pack(fill="x", padx=30, pady=5)
        
        self.toggle_var = ctk.StringVar(value="standard") # Modes: "standard" or "date"
        self.filter_toggle = ctk.CTkSwitch(
            self.toggle_frame, 
            text="Toggle Mode: Off (Sort Category) / On (Time Frame Filter)",
            command=self.handle_toggle_switch,
            variable=self.toggle_var,
            onvalue="date",
            offvalue="standard",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.filter_toggle.pack(side="left", padx=10)

        # --- Settings Frame ---
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.pack(fill="x", padx=30, pady=5)

        # Standard Sorting Widgets - All 5 requested options loaded cleanly
        self.filter_label = ctk.CTkLabel(self.settings_frame, text="Sort Category:")
        self.filter_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.filter_dropdown = ctk.CTkComboBox(self.settings_frame, values=["Best", "Hot", "New", "Top", "Rising"], width=110)
        self.filter_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.filter_dropdown.set("Hot")

        # Date Chronological Widgets
        self.date_label = ctk.CTkLabel(self.settings_frame, text="Time Frame:", text_color="gray")
        self.date_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.date_dropdown = ctk.CTkComboBox(
            self.settings_frame, 
            values=["Past 24 Hours", "Past Week", "Past Month", "Past Year", "All Time"], 
            width=130,
            state="disabled"
        )
        self.date_dropdown.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        self.date_dropdown.set("Past Week")

        # Page Limits Configuration
        self.limit_label = ctk.CTkLabel(self.settings_frame, text="Pages to Scrape:")
        self.limit_label.grid(row=0, column=2, padx=20, pady=10, sticky="e")
        
        self.limit_entry = ctk.CTkEntry(self.settings_frame, width=60)
        self.limit_entry.insert(0, "2")
        self.limit_entry.grid(row=0, column=3, padx=10, pady=10, sticky="w")

        # --- Folder Selection Frame ---
        self.folder_frame = ctk.CTkFrame(self)
        self.folder_frame.pack(fill="x", padx=30, pady=5)

        self.folder_btn = ctk.CTkButton(self.folder_frame, text="Choose Save Folder", command=self.browse_folder, width=150)
        self.folder_btn.pack(side="left", padx=10, pady=10)

        self.folder_label = ctk.CTkLabel(self.folder_frame, text=self.download_directory, wraplength=280, anchor="w", justify="left")
        self.folder_label.pack(side="right", padx=10, pady=10, expand=True, fill="x")

        # --- Download Button ---
        self.download_btn = ctk.CTkButton(self, text="Start Download", font=ctk.CTkFont(size=15, weight="bold"), height=40, fg_color="#ff4500", hover_color="#cc3700", command=self.start_download_thread)
        self.download_btn.pack(fill="x", padx=30, pady=15)

        # --- Output Log Box ---
        self.log_box = ctk.CTkTextbox(self, height=160, state="disabled")
        self.log_box.pack(fill="both", padx=30, pady=(0, 20))

    def handle_toggle_switch(self):
        """Interactively blocks selection properties overlap cross-contamination."""
        if self.toggle_var.get() == "standard":
            self.filter_label.configure(text_color=["black", "white"])
            self.filter_dropdown.configure(state="normal")
            self.date_label.configure(text_color="gray")
            self.date_dropdown.configure(state="disabled")
        else:
            self.filter_label.configure(text_color="gray")
            self.filter_dropdown.configure(state="disabled")
            self.date_label.configure(text_color=["black", "white"])
            self.date_dropdown.configure(state="normal")

    def log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def browse_folder(self):
        selected = filedialog.askdirectory(initialdir=self.download_directory)
        if selected:
            self.download_directory = selected
            self.folder_label.configure(text=selected)

    def start_download_thread(self):
        raw_url = self.sub_entry.get().strip()
        pages_str = self.limit_entry.get().strip()

        if not raw_url:
            messagebox.showerror("Error", "Please enter a valid Reddit URL.")
            return

        if "reddit.com/r/" not in raw_url:
            messagebox.showerror("Error", "Invalid link structure. Make sure it contains 'reddit.com/r/...'")
            return

        if not pages_str.isdigit() or int(pages_str) <= 0:
            messagebox.showerror("Error", "Pages count must be a positive number.")
            return

        try:
            subreddit_name = raw_url.split("/r/")[1].split("/")[0].lower().strip()
        except IndexError:
            messagebox.showerror("Parsing Error", "Could not cleanly isolate the Subreddit name.")
            return

        self.download_btn.configure(state="disabled", text="Scraping...")
        
        filter_mode = self.toggle_var.get()
        filter_value = self.filter_dropdown.get() if filter_mode == "standard" else self.date_dropdown.get()

        threading.Thread(
            target=self.scraper_worker, 
            args=(subreddit_name, filter_mode, filter_value, int(pages_str)), 
            daemon=True
        ).start()

    def scraper_worker(self, subreddit, filter_mode, filter_val, total_pages):
        """Scrapes old.reddit.com switching engine pathways based on selected UI layout criteria."""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        session.cookies.set('over18', '1', domain='.reddit.com')
        
        download_count = 0
        target_path = os.path.join(self.download_directory, subreddit)
        os.makedirs(target_path, exist_ok=True)
        
        self.log(f"🔎 Scanning community: r/{subreddit}")

        # -----------------------------------------------------------------
        # PATHWAY A: Standard Sorting Mechanics (Best/Hot/New/Rising)
        # -----------------------------------------------------------------
        if filter_mode == "standard":
            self.log(f"📊 Filter Profile Active: Sorting by [{filter_val.upper()}]")
            # Map best keyword matching logic to base old.reddit schema loops paths
            sort_token = "hot" if filter_val.lower() == "best" else filter_val.lower()
            current_url = f"https://old.reddit.com/r/{subreddit}/{sort_token}/"

        # -----------------------------------------------------------------
        # PATHWAY B: Chronological UNIX Range Timestamp Search Queries
        # -----------------------------------------------------------------
        else:
            self.log(f"📅 Filter Profile Active: Timeframe [{filter_val}]")
            now = int(time.time())
            seconds_map = {
                "Past 24 Hours": 86400,
                "Past Week": 604800,
                "Past Month": 2592000,
                "Past Year": 31536000
            }
            if filter_val == "All Time":
                search_query = f"subreddit:{subreddit}"
            else:
                start_time = now - seconds_map[filter_val]
                search_query = f"subreddit:{subreddit} AND timestamp:{start_time}..{now}"

            req = session.prepare_request(requests.Request('GET', "https://old.reddit.com/search", params={
                'q': search_query, 'sort': 'new', 'syntax': 'cloudsearch', 'restrict_sr': 'on'
            }))
            current_url = req.url

        # -----------------------------------------------------------------
        # Core Scraping Loop Execution Engine
        # -----------------------------------------------------------------
        for page in range(1, total_pages + 1):
            self.log(f"📄 Fetching page {page} of {total_pages}...")
            try:
                response = session.get(current_url, timeout=10)
                if response.status_code == 429:
                    self.log("⚠️ Reddit is rate-limiting requests. Pausing execution loops.")
                    break
                if response.status_code != 200:
                    self.log(f"❌ Access denied or block hit. Status code: {response.status_code}")
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                posts = soup.find_all('div', class_='thing')
                
                if not posts:
                    self.log("ℹ️ No more matching posts discovered.")
                    break
                
                for post in posts:
                    if 'promoted' in post.get('class', []):
                        continue
                        
                    data_url = post.get('data-url')
                    post_id = post.get('data-fullname', 'img')
                    
                    if data_url:
                        clean_url = data_url.split('?')[0].lower()
                        valid_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
                        
                        if any(clean_url.endswith(ext) for ext in valid_extensions):
                            try:
                                ext = clean_url.split(".")[-1]
                                filename = f"{post_id}.{ext}"
                                file_path = os.path.join(target_path, filename)
                                
                                img_response = session.get(data_url, timeout=10, stream=True)
                                if img_response.status_code == 200:
                                    with open(file_path, "wb") as f:
                                        for chunk in img_response.iter_content(1024):
                                            f.write(chunk)
                                    download_count += 1
                                    self.log(f"✅ Saved: {filename}")
                            except Exception as e:
                                self.log(f"⚠️ Error saving image: {e}")
                
                # Navigate page selectors
                next_button = soup.find('span', class_='next-button')
                if next_button and next_button.find('a'):
                    current_url = next_button.find('a')['href']
                else:
                    self.log("🏁 Reached end of matching records layout index.")
                    break
                    
            except Exception as outer_err:
                self.log(f"❌ Error execution loop break hook: {str(outer_err)}")
                break

        self.log(f"\n🎉 Process Complete! Saved {download_count} images to:\n{target_path}\n")
        self.download_btn.configure(state="normal", text="Start Download")

if __name__ == "__main__":
    app = RedditToggleScraperApp()
    app.mainloop()