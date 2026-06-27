import os
import time
import threading
import requests
import customtkinter as ctk
from tkinter import filedialog, messagebox

# -------------------------------------------------------------------------
# 🔑 OPTIONAL FIXED CONFIGURATION LAYER
# If you fill these in, the UI will automatically load them on startup!
# -------------------------------------------------------------------------
PRE_DEFINED_USERNAME = ""  
PRE_DEFINED_PASSWORD = ""  

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class RedditLoginScraperApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("Reddit Image Downloader (Credentials Mode)")
        self.geometry("560x680")
        self.resizable(False, False)

        # Default Save Directory
        self.download_directory = os.path.join(os.path.expanduser("~"), "Downloads", "RedditDownloads")
        
        self.setup_ui()
        self.check_pre_defined_credentials()
        self.handle_toggle_switch() # Sync initial toggle configuration values state

    def setup_ui(self):
        """Creates and positions all UI widgets."""
        self.title_label = ctk.CTkLabel(self, text="Reddit Image Downloader", font=ctk.CTkFont(size=22, weight="bold"))
        self.title_label.pack(pady=(20, 15))

        # Credentials Input Frame
        self.cred_frame = ctk.CTkFrame(self)
        self.cred_frame.pack(fill="x", padx=30, pady=5)

        self.user_label = ctk.CTkLabel(self.cred_frame, text="Username:", font=ctk.CTkFont(size=12))
        self.user_label.grid(row=0, column=0, padx=10, pady=8, sticky="w")
        self.user_entry = ctk.CTkEntry(self.cred_frame, placeholder_text="Enter Reddit Username", width=150)
        self.user_entry.grid(row=0, column=1, padx=10, pady=8, sticky="w")

        self.pass_label = ctk.CTkLabel(self.cred_frame, text="Password:", font=ctk.CTkFont(size=12))
        self.pass_label.grid(row=0, column=2, padx=10, pady=8, sticky="w")
        self.pass_entry = ctk.CTkEntry(self.cred_frame, placeholder_text="Enter Password", show="*", width=150)
        self.pass_entry.grid(row=0, column=3, padx=10, pady=8, sticky="w")

        # Subreddit URL Input Frame
        self.sub_frame = ctk.CTkFrame(self)
        self.sub_frame.pack(fill="x", padx=30, pady=5)
        
        self.sub_label = ctk.CTkLabel(self.sub_frame, text="Reddit Community URL:", font=ctk.CTkFont(size=13))
        self.sub_label.pack(side="left", padx=10, pady=10)
        self.sub_entry = ctk.CTkEntry(self.sub_frame, placeholder_text="Paste full https://www.reddit.com/r/... URL here", width=250)
        self.sub_entry.pack(side="right", padx=10, pady=10, expand=True, fill="x")

        # NEW: Mode Selector Switch Toggle Layer Control
        self.toggle_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.toggle_frame.pack(fill="x", padx=30, pady=5)
        
        self.toggle_var = ctk.StringVar(value="category") # Options: "category" or "timeframe"
        self.filter_toggle = ctk.CTkSwitch(
            self.toggle_frame, 
            text="Toggle: Off (Sort Category) / On (Time Frame Filter)",
            command=self.handle_toggle_switch,
            variable=self.toggle_var,
            onvalue="timeframe",
            offvalue="category",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.filter_toggle.pack(side="left", padx=10)

        # Settings Frame
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.pack(fill="x", padx=30, pady=5)

        self.filter_label = ctk.CTkLabel(self.settings_frame, text="Sort Category:")
        self.filter_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.filter_dropdown = ctk.CTkComboBox(self.settings_frame, values=["Best", "Hot", "New", "Rising"], width=110)
        self.filter_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.filter_dropdown.set("Hot")

        self.date_label = ctk.CTkLabel(self.settings_frame, text="Time Period:")
        self.date_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.date_dropdown = ctk.CTkComboBox(self.settings_frame, values=["Past 24 Hours", "Past Week", "Past Month", "Past Year", "All Time"], width=130)
        self.date_dropdown.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        self.date_dropdown.set("Past Week")

        self.limit_label = ctk.CTkLabel(self.settings_frame, text="Pages to Scrape:")
        self.limit_label.grid(row=0, column=2, padx=20, pady=10, sticky="e")
        self.limit_entry = ctk.CTkEntry(self.settings_frame, width=60)
        self.limit_entry.insert(0, "2")
        self.limit_entry.grid(row=0, column=3, padx=10, pady=10, sticky="w")

        # Folder Selection Frame
        self.folder_frame = ctk.CTkFrame(self)
        self.folder_frame.pack(fill="x", padx=30, pady=5)

        self.folder_btn = ctk.CTkButton(self.folder_frame, text="Choose Save Folder", command=self.browse_folder, width=150)
        self.folder_btn.pack(side="left", padx=10, pady=10)
        self.folder_label = ctk.CTkLabel(self.folder_frame, text=self.download_directory, wraplength=280, anchor="w", justify="left")
        self.folder_label.pack(side="right", padx=10, pady=10, expand=True, fill="x")

        # Download Button
        self.download_btn = ctk.CTkButton(self, text="Start Download", font=ctk.CTkFont(size=15, weight="bold"), height=40, fg_color="#ff4500", hover_color="#cc3700", command=self.start_download_thread)
        self.download_btn.pack(fill="x", padx=30, pady=15)

        # Output Log Box
        self.log_box = ctk.CTkTextbox(self, height=160, state="disabled")
        self.log_box.pack(fill="both", padx=30, pady=(0, 20))

    def check_pre_defined_credentials(self):
        if PRE_DEFINED_USERNAME:
            self.user_entry.insert(0, PRE_DEFINED_USERNAME)
        if PRE_DEFINED_PASSWORD:
            self.pass_entry.insert(0, PRE_DEFINED_PASSWORD)

    def handle_toggle_switch(self):
        """Disables the unused selection pathway interactively to block overlap requests."""
        if self.toggle_var.get() == "category":
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
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()
        raw_url = self.sub_entry.get().strip()
        pages_str = self.limit_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Credentials Error", "Please provide account entries details values.")
            return

        if not raw_url or "reddit.com/r/" not in raw_url:
            messagebox.showerror("Error", "Please enter a valid Reddit URL.")
            return

        if not pages_str.isdigit() or int(pages_str) <= 0:
            messagebox.showerror("Error", "Page count must be a positive integer.")
            return

        try:
            subreddit_name = raw_url.split("/r/")[1].split("/")[0].lower().strip()
        except IndexError:
            messagebox.showerror("Parsing Error", "Could not cleanly isolate Subreddit name.")
            return

        self.download_btn.configure(state="disabled", text="Logging In...")
        threading.Thread(
            target=self.login_and_scrape_worker, 
            args=(username, password, subreddit_name, self.toggle_var.get(), self.filter_dropdown.get(), self.date_dropdown.get(), int(pages_str)), 
            daemon=True
        ).start()

    def process_gallery(self, session, post_data, base_post_path):
        saved_images = 0
        if 'gallery_data' in post_data and 'media_metadata' in post_data:
            os.makedirs(base_post_path, exist_ok=True)
            for idx, item in enumerate(post_data['gallery_data']['items'], start=1):
                media_id = item['media_id']
                if media_id in post_data['media_metadata']:
                    meta = post_data['media_metadata'][media_id]
                    if meta.get('status') == 'valid' and 's' in meta:
                        img_url = meta['s'].get('u', '').replace('&amp;', '&')
                        if img_url:
                            ext = img_url.split('?')[0].split('.')[-1]
                            file_path = os.path.join(base_post_path, f"image_{idx}.{ext}")
                            res = session.get(img_url, timeout=10)
                            if res.status_code == 200:
                                with open(file_path, "wb") as f:
                                    f.write(res.content)
                                saved_images += 1
        return saved_images

    def login_and_scrape_worker(self, username, password, subreddit, mode, sort_val, time_val, total_pages):
        session = requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36'})

        self.log(f"🔐 Authenticating secure token mapping for [{username}]...")
        try:
            auth_resp = session.post("https://www.reddit.com/api/v1/access_token", auth=('client_id', ''), data={'grant_type': 'password', 'username': username, 'password': password}, timeout=10)
            auth_data = auth_resp.json()
            if "access_token" in auth_data:
                session.headers.update({'Authorization': f"bearer {auth_data['access_token']}"})
            session.cookies.set('over18', '1', domain='.reddit.com')
            self.log("✅ Authenticated payload cleared.")
        except Exception as e:
            self.log(f"❌ Handshake failed: {e}")
            self.download_btn.configure(state="normal", text="Start Download")
            return

        # Dynamically build routing endpoint matching active toggle pathway selections
        if mode == "category":
            sort_path = "hot" if sort_val.lower() == "best" else sort_val.lower()
            base_json_url = f"https://www.reddit.com/r/{subreddit}/{sort_path}.json"
            self.log(f"📊 Mode active: Category [{sort_val.upper()}]")
        else:
            base_json_url = f"https://www.reddit.com/r/{subreddit}/top.json"
            self.log(f"📅 Mode active: Time Period [{time_val}]")

        time_map = {"Past 24 Hours": "hour", "Past Week": "week", "Past Month": "month", "Past Year": "year", "All Time": "all"}
        download_count, gallery_counter = 0, 1
        target_path = os.path.join(self.download_directory, subreddit)
        os.makedirs(target_path, exist_ok=True)

        current_after = None
        
        # Core constraint loop tracking absolute loop boundaries correctly
        for page in range(1, total_pages + 1):
            self.log(f"📄 Processing page {page} of {total_pages}...")
            params = {'limit': 100}
            if mode == "timeframe":
                params['t'] = time_map[time_val]
            if current_after:
                params['after'] = current_after

            try:
                res = session.get(base_json_url, params=params, timeout=10)
                if res.status_code == 200:
                    data_payload = res.json().get('data', {})
                    current_after = data_payload.get('after')
                    listing_data = data_payload.get('children', [])
                    
                    if not listing_data:
                        self.log("ℹ️ No more matching records on this tracking page node index.")
                        break

                    for child in listing_data:
                        post_data = child.get('data', {})
                        data_url = post_data.get('url', '')
                        
                        if post_data.get('is_gallery', False) or "reddit.com/gallery/" in data_url:
                            post_folder = os.path.join(target_path, f"multi_{gallery_counter}")
                            saved_g = self.process_gallery(session, post_data, post_folder)
                            if saved_g > 0:
                                download_count += saved_g
                                self.log(f"📁 Created folder: multi_{gallery_counter} ({saved_g} images)")
                                gallery_counter += 1
                        elif data_url and any(data_url.split('?')[0].lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]):
                            ext = data_url.split('?')[0].split('.')[-1]
                            file_path = os.path.join(target_path, f"{post_data.get('name', 'img')}.{ext}")
                            img_res = session.get(data_url, timeout=10)
                            if img_res.status_code == 200:
                                with open(file_path, "wb") as f:
                                    f.write(img_res.content)
                                download_count += 1
                                self.log(f"✅ Saved Single Image: {post_data.get('name')}.{ext}")
                    
                    if not current_after:
                        break
                else:
                    self.log(f"❌ Server Error: {res.status_code}")
                    break
            except Exception as err:
                self.log(f"❌ Scraping error layer flags: {str(err)}")
                break

        self.log(f"\n🎉 Complete! Saved {download_count} total files down to:\n{target_path}\n")
        self.download_btn.configure(state="normal", text="Start Download")

if __name__ == "__main__":
    app = RedditLoginScraperApp()
    app.mainloop()