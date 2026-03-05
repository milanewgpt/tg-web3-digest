1) Create folder and venv
   sudo mkdir -p /opt/tg-web3-digest
   sudo chown -R $USER:$USER /opt/tg-web3-digest
   cd /opt/tg-web3-digest

   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2) Put files into /opt/tg-web3-digest
   - tg_digest_collector.py
   - tg_digest_sender.py
   - db_init.py
   - requirements.txt
   - .env (copy from .env.example and fill values)
   - If you want all Reader-subscribed public channels, set:
     TG_CHANNELS=ALL

3) Initialize DB
   source .venv/bin/activate
   export $(grep -v '^#' .env | xargs)
   python3 db_init.py

4) First Telethon login (Reader account)
   source .venv/bin/activate
   export $(grep -v '^#' .env | xargs)
   python3 tg_digest_sender.py

   On first run, Telethon will ask for phone + code in console.
   Use the READER account phone.
   This creates the session file: reader_session.session in the working dir.
   Keep it safe.

5) Test manually
   Run collector for 15-30 minutes:
     python3 tg_digest_collector.py
   Stop with Ctrl+C
   Send digest:
     python3 tg_digest_sender.py
   Confirm digest appears in your private group.

6) Set server timezone
   sudo timedatectl set-timezone Asia/Jerusalem

7) Install systemd services
   Copy unit files:
     sudo cp systemd/*.service /etc/systemd/system/
     sudo cp systemd/*.timer   /etc/systemd/system/
   Reload:
     sudo systemctl daemon-reload

   NOTE: Collector script already sleeps by POLL_SECONDS.
   Recommended simple mode:
   - Enable tg-collector.service
   - Do NOT enable tg-collector.timer

   Enable collector as a service:
     sudo systemctl enable --now tg-collector.service

   Enable timers:
     sudo systemctl enable --now tg-digest-0800.timer
     sudo systemctl enable --now tg-digest-1100.timer
     sudo systemctl enable --now tg-digest-1400.timer
     sudo systemctl enable --now tg-digest-1900.timer

8) Check status/logs
   sudo systemctl status tg-collector.service
   sudo journalctl -u tg-collector.service -n 200 --no-pager

   sudo systemctl list-timers --all | grep tg-digest
   sudo journalctl -u tg-digest-0800.service -n 200 --no-pager

TUNING
- If Reader is in MANY channels, increase POLL_SECONDS to 900-1200.
- If you see FloodWait, do NOT reduce intervals; increase them.
- Keep TG_CHANNELS limited to channels you truly want.

OPTIONAL: Make digest smarter later
- Replace heuristic scoring with LLM summarization once the pipeline is stable.

ONE-LINER QUICK START (for Cursor to execute)
# 0) Ensure you are on the server as a user with sudo.
# 1) Create folder + venv + install deps:
sudo mkdir -p /opt/tg-web3-digest && sudo chown -R $USER:$USER /opt/tg-web3-digest && cd /opt/tg-web3-digest && \
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

# 2) Create .env from .env.example, fill values, then:
source .venv/bin/activate && export $(grep -v '^#' .env | xargs) && python3 db_init.py

# 3) First login run (Reader):
source .venv/bin/activate && export $(grep -v '^#' .env | xargs) && python3 tg_digest_sender.py

# 4) Install systemd units:
sudo timedatectl set-timezone Asia/Jerusalem && \
sudo cp systemd/*.service /etc/systemd/system/ && sudo cp systemd/*.timer /etc/systemd/system/ && \
sudo systemctl daemon-reload && \
sudo systemctl enable --now tg-collector.service && \
sudo systemctl enable --now tg-digest-0800.timer tg-digest-1100.timer tg-digest-1400.timer tg-digest-1900.timer

IMPORTANT: What you must fill before running
- TG_API_ID / TG_API_HASH (from https://my.telegram.org)
- TG_CHANNELS (public channels where Reader is already a member)
- TG_TARGET (exact private group name, must include Reader + main)
- Server path in DB_PATH must match /opt/tg-web3-digest/...
