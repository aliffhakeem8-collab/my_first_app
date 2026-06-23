import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import yfinance as yf
from datetime import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import webbrowser
import futu as ft

# Global variables to track state
is_monitoring = False
target_ticker = ""
min_target_price = 0.0
max_target_price = 0.0
x_link_url = ""

def analyze_ticker():
    raw_input = ticker_entry.get().upper().strip()
    if not raw_input:
        status_label.config(text="Error: Enter a ticker symbol first.", fg="#f38ba8")
        return
    
    if raw_input.isdigit() and len(raw_input) == 4:
        ticker = f"{raw_input}.KL"
        ticker_entry.delete(0, tk.END)
        ticker_entry.insert(0, ticker)
    else:
        ticker = raw_input
    
    status_label.config(text=f"Pulling multi-source news & spot data for {ticker}...", fg="#89b4fa")
    root.update_idletasks()
    
    try:
        stock = yf.Ticker(ticker)
        current_spot = stock.fast_info['last_price']
        
        price_display_lbl.config(text=f"RM {round(current_spot, 2)}" if ".KL" in ticker else f"${round(current_spot, 2)}")
        
        min_buffer = round(current_spot * 0.98, 2)
        max_buffer = round(current_spot * 1.02, 2)
        
        min_price_entry.delete(0, tk.END)
        min_price_entry.insert(0, str(min_buffer))
        
        max_price_entry.delete(0, tk.END)
        max_price_entry.insert(0, str(max_buffer))
        
        compile_multi_source_news(ticker, stock)
        status_label.config(text=f"Analysis complete for {ticker}.", fg="#a6e3a1")
        
    except Exception as e:
        status_label.config(text="Analysis failed. Check ticker connection.", fg="#f38ba8")

def compile_multi_source_news(ticker, stock_obj):
    news_text_box.config(state="normal")
    news_text_box.delete("1.0", tk.END)
    search_term = ticker.replace(".KL", "")
    is_malaysian = ".KL" in ticker
    
    news_text_box.insert(tk.END, "=== YAHOO FINANCE ===\n", "source_header")
    try:
        raw_news = stock_obj.news
        if not raw_news:
            news_text_box.insert(tk.END, "• No structural feeds available on Yahoo.\n", "body_text")
        else:
            for story in raw_news[:2]:
                title = story.get('title', 'No Title')
                pub = story.get('publisher', 'Yahoo Finance')
                news_text_box.insert(tk.END, f"• {title}\n", "headline")
                news_text_box.insert(tk.END, f"  Source: {pub}\n\n", "source_meta")
    except Exception:
        news_text_box.insert(tk.END, "• Failed to acquire Yahoo stream.\n\n", "body_text")
        
    news_text_box.insert(tk.END, "=== GOOGLE NEWS ===\n", "source_header")
    try:
        loc_query = f"{search_term} bursa malaysia stock" if is_malaysian else f"${ticker} stock market"
        query = urllib.parse.quote(loc_query)
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-MY&gl=MY&ceid=MY:en" if is_malaysian else f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        
        req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root_xml = ET.fromstring(xml_data)
        items = root_xml.findall('.//item')
        
        if not items:
            news_text_box.insert(tk.END, "• No recent Google News items found.\n", "body_text")
        else:
            for item in items[:2]:
                raw_title = item.find('title').text if item.find('title') is not None else "No Title"
                title_parts = raw_title.split(" - ")
                clean_title = " - ".join(title_parts[:-1]) if len(title_parts) > 1 else raw_title
                source = title_parts[-1] if len(title_parts) > 1 else "Google News"
                news_text_box.insert(tk.END, f"• {clean_title}\n", "headline")
                news_text_box.insert(tk.END, f"  Source: {source}\n\n", "source_meta")
    except Exception:
        news_text_box.insert(tk.END, "• Failed to parse Google RSS pipeline.\n\n", "body_text")

    news_text_box.insert(tk.END, "=== X (TWITTER) STREAM ===\n", "source_header")
    news_text_box.insert(tk.END, f"• Real-time social velocity tracking ready for {ticker}.\n", "headline")
    
    global x_link_url
    x_link_url = f"https://x.com/search?q=%23{search_term}&f=live" if is_malaysian else f"https://x.com/search?q=%24{ticker}&f=live"
    news_text_box.insert(tk.END, "  [ CLICK HERE TO VIEW LIVE X FEED ]\n\n", "hyperlink")
    news_text_box.config(state="disabled")

def open_x_browser(event):
    global x_link_url
    if x_link_url:
        webbrowser.open_new_tab(x_link_url)

def start_monitoring():
    global is_monitoring, target_ticker, min_target_price, max_target_price
    
    ticker = ticker_entry.get().upper().strip()
    min_p_str = min_price_entry.get().strip()
    max_p_str = max_price_entry.get().strip()
    
    if not ticker:
        status_label.config(text="Error: Enter a valid Ticker Symbol.", fg="#f38ba8")
        return
    try:
        min_p = float(min_p_str)
        max_p = float(max_p_str)
        if min_p >= max_p or min_p <= 0:
            raise ValueError
    except ValueError:
        status_label.config(text="Error: Max price must be greater than Min.", fg="#f38ba8")
        return
        
    target_ticker = ticker
    min_target_price = min_p
    max_target_price = max_p
    is_monitoring = True
    
    ticker_entry.config(state="disabled")
    min_price_entry.config(state="disabled")
    max_price_entry.config(state="disabled")
    shares_combo.config(state="disabled")
    mode_paper_rb.config(state="disabled")
    mode_real_rb.config(state="disabled")
    analyze_btn.config(state="disabled", bg="#313244", fg="#6c7086")
    start_btn.config(state="disabled", text="SCANNING MARKET...", bg="#45475a")
    
    currency_symbol = "RM" if ".KL" in target_ticker else "$"
    status_label.config(text=f"WATCHING: {target_ticker} [{currency_symbol}{min_target_price} - {currency_symbol}{max_target_price}]", fg="#fab387")
    check_market_loop()

def check_market_loop():
    global is_monitoring, target_ticker, min_target_price, max_target_price
    if not is_monitoring:
        return
        
    try:
        stock = yf.Ticker(target_ticker)
        current_price = stock.fast_info['last_price']
        
        currency_symbol = "RM " if ".KL" in target_ticker else "$"
        price_display_lbl.config(text=f"{currency_symbol}{round(current_price, 2)}")
        status_label.config(text=f"Scanning live... Current: {currency_symbol}{round(current_price, 2)}", fg="#89b4fa")
        
        if min_target_price <= current_price <= max_target_price:
            is_monitoring = False 
            show_custom_trigger_window(current_price)
            return
    except Exception:
        status_label.config(text="Scan Error. Retrying...", fg="#f38ba8")
        
    if is_monitoring:
        root.after(5000, check_market_loop)

def show_custom_trigger_window(hit_price):
    alert_win = tk.Toplevel(root)
    alert_win.title("Target Range Notification")
    alert_win.geometry("380x350")
    alert_win.configure(bg="#11111b")
    alert_win.transient(root)
    alert_win.grab_set()
    
    x = root.winfo_x() + (root.winfo_width() // 2) - (380 // 2)
    y = root.winfo_y() + (root.winfo_height() // 2) - (350 // 2)
    alert_win.geometry(f"+{x}+{y}")
    
    selected_mode = "REAL LIVE CASH TRADE" if env_var.get() == "REAL" else "PAPER TRADING MOCK"
    mode_color = "#f38ba8" if env_var.get() == "REAL" else "#a6e3a1"
    
    tk.Label(alert_win, text="TARGET MATCH DETECTED", font=("Segoe UI", 13, "bold"), bg="#11111b", fg="#fab387").pack(pady=(20, 5))
    tk.Label(alert_win, text=f"[{selected_mode} MODE]", font=("Segoe UI", 10, "bold"), bg="#11111b", fg=mode_color).pack(pady=(0, 10))
    
    info_box = tk.Frame(alert_win, bg="#1e1e2e", highlightbackground="#313244", highlightthickness=1)
    info_box.pack(fill="x", padx=30, pady=5, ipady=12)
    
    def add_alert_row(label, val, val_color="#ffffff"):
        r = tk.Frame(info_box, bg="#1e1e2e")
        r.pack(fill="x", padx=15, pady=4)
        tk.Label(r, text=label, font=FONT_REGULAR, bg="#1e1e2e", fg="#a6adc8").pack(side=tk.LEFT)
        tk.Label(r, text=val, font=FONT_BOLD, bg="#1e1e2e", fg=val_color).pack(side=tk.RIGHT)

    currency_symbol = "RM " if ".KL" in target_ticker else "$"
    add_alert_row("Target Asset:", target_ticker)
    add_alert_row("Trigger Value:", f"{currency_symbol}{round(hit_price, 2)}", "#a6e3a1")
    add_alert_row("Defined Bounds:", f"{currency_symbol}{min_target_price} - {currency_symbol}{max_target_price}")

    def fire_order_to_moomoo():
        # SAFETY CHECK
        if env_var.get() == "REAL":
            if not messagebox.askyesno("CONFIRMATION", "WARNING: You are about to place a REAL money trade in Moomoo. Are you sure?"):
                status_label.config(text="Order cancelled by user.", fg="#ffb86c")
                reset_interface()
                return

        try:
            trade_ctx = ft.OpenSecTradeContext(host="127.0.0.1", port=11111)
            trade_ctx.start()
            
            raw_ticker = target_ticker.upper().strip()
            moomoo_symbol = f"MY.{raw_ticker.replace('.KL', '')}" if ".KL" in raw_ticker else f"US.{raw_ticker}"
            
            status_label.config(text="Synchronizing OpenD user identity...", fg="#89b4fa")
            root.update_idletasks()
            
            chosen_env = ft.TrdEnv.REAL if env_var.get() == "REAL" else ft.TrdEnv.SIMULATE
            
            ret_acc, acc_data = trade_ctx.get_acc_list()
            target_acc_id = None
            
            if ret_acc == ft.RET_OK and not acc_data.empty:
                env_filtered = acc_data[acc_data['trd_env'] == chosen_env]
                for _, row in env_filtered.iterrows():
                    # Skip the restricted Global Account
                    if str(row['acc_id']) != "3251871":
                        target_acc_id = row['acc_id']
                        break
                if not target_acc_id and not env_filtered.empty:
                    target_acc_id = env_filtered.iloc[0]['acc_id']

            order_args = {
                "price": 0,
                "qty": int(shares_combo.get()),
                "code": moomoo_symbol,
                "trd_side": ft.TrdSide.BUY,
                "order_type": ft.OrderType.MARKET,
                "trd_env": chosen_env,
                "acc_id": target_acc_id
            }
            
            root.update_idletasks()
            ret, data = trade_ctx.place_order(**order_args)
            
            if ret == ft.RET_OK:
                status_label.config(text=f"Success: Ordered {shares_combo.get()} shares!", fg="#a6e3a1")
            else:
                error_msg = data.iloc[0]['error_str'] if (hasattr(data, 'empty') and not data.empty) else str(data)
                status_label.config(text=f"Moomoo Rejected: {error_msg}", fg="#f38ba8")
                
            trade_ctx.close()
        except Exception as e:
            status_label.config(text=f"Network Pipe Error: {str(e)}", fg="#f38ba8")
        reset_interface()

    def handle_modal_execute():
        alert_win.destroy()
        fire_order_to_moomoo()

    def handle_modal_ignore():
        alert_win.destroy()
        reset_interface()

    btn_frame = tk.Frame(alert_win, bg="#11111b")
    btn_frame.pack(fill="x", padx=30, pady=(15, 0))
    
    tk.Button(btn_frame, text="IGNORE / RESET", font=FONT_BOLD, bg="#313244", fg="#f38ba8", bd=0, command=handle_modal_ignore, cursor="hand2").pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 8), ipady=8)
    tk.Button(btn_frame, text="EXECUTE", font=FONT_BOLD, bg="#1e66f5", fg="#ffffff", bd=0, command=handle_modal_execute, cursor="hand2").pack(side=tk.LEFT, fill="x", expand=True, ipady=8)

def reset_interface():
    ticker_entry.config(state="normal")
    min_price_entry.config(state="normal")
    max_price_entry.config(state="normal")
    shares_combo.config(state="normal")
    mode_paper_rb.config(state="normal")
    mode_real_rb.config(state="normal")
    analyze_btn.config(state="normal", bg="#fab387", fg="#11111b")
    start_btn.config(state="normal", text="START MONITORING LOOP", bg="#1e66f5")
    price_display_lbl.config(text="---")

def _on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

root = tk.Tk()
root.title("Nexus Automated Range Trigger")
root.geometry("480x750")
root.configure(bg="#11111b")

style = ttk.Style()
style.theme_use("clam")
style.configure("Custom.TLabelframe", background="#1e1e2e", bordercolor="#313244", borderwidth=1)
style.configure("Custom.TLabelframe.Label", font=("Segoe UI", 11, "bold"), background="#1e1e2e", foreground="#89b4fa")
style.configure("TEntry", fieldbackground="#313244", foreground="#ffffff", bordercolor="#45475a", relief="flat")
style.configure("TCombobox", fieldbackground="#313244", background="#313244", foreground="#ffffff")

FONT_REGULAR = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")

scrollbar = ttk.Scrollbar(root, orient="vertical")
scrollbar.pack(side=tk.RIGHT, fill="y")

canvas = tk.Canvas(root, bg="#11111b", bd=0, highlightthickness=0, yscrollcommand=scrollbar.set)
canvas.pack(side=tk.LEFT, fill="both", expand=True)
scrollbar.config(command=canvas.yview)

scroll_content_frame = tk.Frame(canvas, bg="#11111b")
canvas_window = canvas.create_window((0, 0), window=scroll_content_frame, anchor="nw")

def configure_scroll_region(event):
    canvas.configure(scrollregion=canvas.bbox("all"))
scroll_content_frame.bind("<Configure>", configure_scroll_region)

def keep_frame_width(event):
    canvas.itemconfigure(canvas_window, width=event.width)
canvas.bind("<Configure>", keep_frame_width)

root.bind_all("<MouseWheel>", _on_mousewheel)

tk.Label(scroll_content_frame, text="A U T O M A T E D  T R I G G E R", font=("Segoe UI", 15, "bold"), bg="#11111b", fg="#cdd6f4").pack(pady=15)

setup_frame = ttk.LabelFrame(scroll_content_frame, text=" TARGET RANGE SETUP ", style="Custom.TLabelframe")
setup_frame.pack(fill="x", padx=25, pady=5, ipady=8)

tk.Label(setup_frame, text="Ticker Symbol:", font=FONT_REGULAR, bg="#1e1e2e", fg="#a6adc8").grid(row=0, column=0, padx=15, pady=6, sticky="w")
ticker_entry = ttk.Entry(setup_frame, font=FONT_BOLD, width=12)
ticker_entry.grid(row=0, column=1, padx=15, pady=6, sticky="w", ipady=3)
ticker_entry.insert(0, "1155")

analyze_btn = tk.Button(setup_frame, text="ANALYZE", font=FONT_BOLD, bg="#fab387", fg="#11111b", bd=0, cursor="hand2", command=analyze_ticker)
analyze_btn.grid(row=0, column=2, padx=5, pady=6, sticky="w", ipadx=12, ipady=2)

tk.Label(setup_frame, text="Min Price Floor:", font=FONT_REGULAR, bg="#1e1e2e", fg="#a6adc8").grid(row=1, column=0, padx=15, pady=6, sticky="w")
min_price_entry = ttk.Entry(setup_frame, font=FONT_REGULAR, width=12)
min_price_entry.grid(row=1, column=1, padx=15, pady=6, sticky="w", ipady=3)

tk.Label(setup_frame, text="Max Price Ceiling:", font=FONT_REGULAR, bg="#1e1e2e", fg="#a6adc8").grid(row=2, column=0, padx=15, pady=6, sticky="w")
max_price_entry = ttk.Entry(setup_frame, font=FONT_REGULAR, width=12)
max_price_entry.grid(row=2, column=1, padx=15, pady=6, sticky="w", ipady=3)

tk.Label(setup_frame, text="Shares to Buy:", font=FONT_REGULAR, bg="#1e1e2e", fg="#a6adc8").grid(row=3, column=0, padx=15, pady=6, sticky="w")
shares_combo = ttk.Combobox(setup_frame, font=FONT_BOLD, width=10, values=["100", "500", "1000", "2000", "5000"])
shares_combo.grid(row=3, column=1, padx=15, pady=6, sticky="w")
shares_combo.current(0)

tk.Label(setup_frame, text="Execution Engine:", font=FONT_REGULAR, bg="#1e1e2e", fg="#a6adc8").grid(row=4, column=0, padx=15, pady=6, sticky="w")
env_var = tk.StringVar(value="PAPER")
mode_panel = tk.Frame(setup_frame, bg="#1e1e2e")
mode_panel.grid(row=4, column=1, columnspan=2, padx=15, pady=6, sticky="w")
mode_paper_rb = tk.Radiobutton(mode_panel, text="Paper Trade", variable=env_var, value="PAPER", font=FONT_BOLD, bg="#1e1e2e", fg="#cdd6f4", selectcolor="#313244")
mode_paper_rb.pack(side=tk.LEFT, padx=(0, 10))
mode_real_rb = tk.Radiobutton(mode_panel, text="Real Trade (Live)", variable=env_var, value="REAL", font=FONT_BOLD, bg="#1e1e2e", fg="#cdd6f4", selectcolor="#313244")
mode_real_rb.pack(side=tk.LEFT)

news_frame = ttk.LabelFrame(scroll_content_frame, text=" LIVE FEED (YAHOO | GOOGLE | X) ", style="Custom.TLabelframe")
news_frame.pack(fill="x", padx=25, pady=10, ipady=5)
news_text_box = tk.Text(news_frame, bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 9), bd=0, wrap=tk.WORD, height=10)
news_text_box.pack(fill="x", padx=12, pady=10)
news_text_box.tag_configure("source_header", font=("Segoe UI", 10, "bold"), foreground="#89b4fa")
news_text_box.tag_configure("headline", font=("Segoe UI", 9, "bold"), foreground="#cdd6f4")
news_text_box.tag_configure("source_meta", font=("Segoe UI", 8, "italic"), foreground="#6c7086")
news_text_box.tag_configure("hyperlink", font=("Segoe UI", 9, "bold", "underline"), foreground="#fab387")
news_text_box.tag_bind("hyperlink", "<Button-1>", open_x_browser)

monitor_frame = ttk.LabelFrame(scroll_content_frame, text=" AUTOMATED MONITORING DATA ", style="Custom.TLabelframe")
monitor_frame.pack(fill="x", padx=25, pady=5, ipady=5)
display_row = tk.Frame(monitor_frame, bg="#1e1e2e")
display_row.pack(fill="x", padx=15, pady=5)
tk.Label(display_row, text="Live Captured Price:", font=FONT_REGULAR, bg="#1e1e2e", fg="#cdd6f4").pack(side=tk.LEFT)
price_display_lbl = tk.Label(display_row, text="---", font=("Segoe UI", 14, "bold"), bg="#1e1e2e", fg="#ffffff")
price_display_lbl.pack(side=tk.RIGHT)

status_label = tk.Label(scroll_content_frame, text="System Ready.", font=("Segoe UI", 9, "italic"), bg="#11111b", fg="#6c7086")
status_label.pack(pady=5)

start_btn = tk.Button(scroll_content_frame, text="START MONITORING LOOP", font=("Segoe UI", 11, "bold"), bg="#1e66f5", fg="#ffffff", bd=0, cursor="hand2", command=start_monitoring)
start_btn.pack(fill="x", padx=25, pady=10, ipady=10)

root.mainloop()