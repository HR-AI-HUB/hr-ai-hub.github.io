# BigBlueButton + Greenlight v3 Setup Guide

A step-by-step installation guide for deploying BigBlueButton (BBB) with the Greenlight v3 web frontend on a SURF Research Cloud (or similar Ubuntu 22.04) virtual machine. Written for data scientists and researchers with basic Linux familiarity.

---

## Prerequisites

Before you begin, make sure you have:

- A **fresh Ubuntu 22.04 LTS** server (VM or bare metal)
- Minimum **4 CPU cores**, **8 GB RAM** (16 GB recommended), **50 GB disk**
- A **fully qualified domain name (FQDN)** pointing to your server's public IP (e.g. `cyberroom.example.nl`)
- Port **80** and **443** open in your firewall
- Root or `sudo` access via SSH
- A valid **email address** for the SSL certificate

> ⚠️ BigBlueButton requires a dedicated domain name — it cannot run on an IP address alone.

---

## Part 1: Install BigBlueButton

### Step 1 — Verify your server meets requirements

```bash
# Check Ubuntu version (must be 22.04)
lsb_release -a

# Check available RAM (need at least 8 GB)
free -h

# Check CPU cores (need at least 4)
nproc

# Check that your domain resolves to this server's IP
hostname -I
dig +short yourdomain.example.nl
```

Both IPs must match before proceeding.

### Step 2 — Run the BBB install script

BigBlueButton provides an official install script that handles everything automatically.

```bash
wget -qO- https://raw.githubusercontent.com/bigbluebutton/bbb-install/v3.0.x-release/bbb-install.sh | bash -s -- \
  -v focal-300 \
  -s yourdomain.example.nl \
  -e your@email.nl \
  -w
```

**Flag reference:**

| Flag | Meaning |
|------|---------|
| `-v focal-300` | Install BBB version 3.0 |
| `-s yourdomain.example.nl` | Your server's FQDN |
| `-e your@email.nl` | Email for Let's Encrypt SSL certificate |
| `-w` | Install the demo rooms (optional, useful for testing) |

This takes **15–30 minutes**. The script installs BBB, nginx, and obtains an SSL certificate automatically.

### Step 3 — Verify the installation

```bash
# Check all BBB services are running
sudo bbb-conf --status

# Run a full health check
sudo bbb-conf --check

# Get your BBB API endpoint and secret (save these!)
sudo bbb-conf --secret
```

The `--secret` command outputs something like:

```
URL: https://yourdomain.example.nl/bigbluebutton/
Secret: abc123xyzSECRETKEY456
```

**Save both values** — you will need them for Greenlight configuration.

### Step 4 — Test in the browser

Open `https://yourdomain.example.nl` in your browser. You should see the BBB demo page. If you see a green lock icon and no certificate warnings, the SSL setup worked correctly.

---

## Part 2: Install Greenlight v3

Greenlight v3 is the official web frontend for BigBlueButton. It provides user accounts, rooms management, and a meeting launcher. It runs as a set of Docker containers.

### Step 1 — Install Docker

```bash
# Update package list
sudo apt update

# Install prerequisites
sudo apt install -y ca-certificates curl gnupg

# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine and Compose plugin
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add your user to the docker group (avoid needing sudo every time)
sudo usermod -aG docker $USER
newgrp docker

# Verify Docker works
docker --version
docker compose version
```

### Step 2 — Create the Greenlight directory

```bash
mkdir ~/greenlight
cd ~/greenlight
```

### Step 3 — Create the `.env` configuration file

```bash
nano ~/greenlight/.env
```

Paste the following content, replacing the placeholder values with your own:

```env
# BigBlueButton connection — from: sudo bbb-conf --secret
BIGBLUEBUTTON_ENDPOINT=https://yourdomain.example.nl/bigbluebutton/
BIGBLUEBUTTON_SECRET=your_bbb_secret_here

# Generate a secure secret key (run: openssl rand -hex 64)
SECRET_KEY_BASE=paste_output_of_openssl_rand_hex_64_here

# URL path where Greenlight will be served
RELATIVE_URL_ROOT=/gl

# PostgreSQL database settings
POSTGRES_PASSWORD=choose_a_strong_password_here
POSTGRES_PORT=5432
POSTGRES_USERNAME=postgres
POSTGRES_NAME=greenlight-v3-production
POSTGRES_HOST=postgres
POSTGRES_URL=postgresql://postgres:choose_a_strong_password_here@postgres:5432/greenlight-v3-production

# DATABASE_URL must explicitly be set (Rails reads this, not POSTGRES_URL)
DATABASE_URL=postgresql://postgres:choose_a_strong_password_here@postgres:5432/greenlight-v3-production

# Redis settings
REDIS_URL=redis://redis:6379

# Locale and timezone
DEFAULT_LOCALE=en
DEFAULT_TIMEZONE=Europe/Amsterdam

# Allow users to self-register
ALLOW_GREENLIGHT_ACCOUNTS=true
```

To  change a specific **PARAMETER** in .env file use:

```bash
echo "ALLOW_GREENLIGHT_ACCOUNTS=false" >> ~/greenlight/.env
docker compose -f ~/greenlight/docker-compose.yml restart greenlight-v3
```

> ⚠️ The `DATABASE_URL` and `POSTGRES_URL` must contain the **same password**. If you change `POSTGRES_PASSWORD`, update both URLs.

Generate a secure `SECRET_KEY_BASE`:

```bash
openssl rand -hex 64
```

Copy the output and paste it as the value for `SECRET_KEY_BASE` in `.env`.

### Step 4 — Create the `docker-compose.yml` file

```bash
nano ~/greenlight/docker-compose.yml
```

Paste the following:

```yaml
services:
  postgres:
    image: postgres:14.6-alpine3.17
    container_name: postgres
    restart: unless-stopped
    volumes:
      - ./data/postgres/14/database_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=choose_a_strong_password_here

  redis:
    image: redis:6.2-alpine3.17
    container_name: redis
    restart: unless-stopped
    volumes:
      - ./data/redis/database_data:/data

  greenlight-v3:
    image: bigbluebutton/greenlight:v3
    container_name: greenlight-v3
    restart: unless-stopped
    env_file: .env
    environment:
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - FORCE_SSL=false
      - DATABASE_URL=${DATABASE_URL}
    ports:
      - 127.0.0.1:5050:3000
    depends_on:
      - postgres
      - redis
```

> ⚠️ Replace `choose_a_strong_password_here` in `POSTGRES_PASSWORD` with the same password you used in `.env`.

### Step 5 — Start the containers

```bash
cd ~/greenlight
docker compose up -d

# Wait for PostgreSQL to fully start
sleep 15

# Confirm all containers are running
docker ps
```

You should see three containers running: `postgres`, `redis`, and `greenlight-v3`.

### Step 6 — Initialize the database

```bash
# Create and migrate the database schema
docker exec -it greenlight-v3 bundle exec rake db:create db:migrate

# Run data migrations (populates roles, settings, permissions)
docker exec -it greenlight-v3 bundle exec rake data:migrate
```

> ℹ️ Both commands should complete without errors. The `data:migrate` step populates default settings, roles, meeting options, and permissions that Greenlight needs to function.

### Step 7 — Create the admin account

```bash
docker exec -it greenlight-v3 bundle exec rails console
```

Inside the Rails console, run:

```ruby
role = Role.find_by(name: 'Administrator')
u = User.new(
  name: 'Admin',
  email: 'admin@yourdomain.nl',
  password: 'ChooseAStrongPassword123!',
  password_confirmation: 'ChooseAStrongPassword123!',
  role: role,
  provider: role.provider,
  verified: true,
  status: 1
)
u.save!
puts "Admin created!"
exit
```

Replace `admin@yourdomain.nl` and the password with your own values. **Write down the password — you will need it to log in.**

---

### Step 7a — Enable GUI to create a new room
```bash
docker exec -it greenlight-v3 bundle exec rails console
```

Inside the Rails console, run:

```ruby
perm = Permission.find_by(name: 'CreateRoom')

Role.all.each do |role|
  rp = RolePermission.find_or_initialize_by(role: role, permission: perm)
  rp.value = 'true'
  rp.save(validate: false)
  puts "Enabled CreateRoom for role: #{role.name}"
end
exit
```

The save (validate: false) bypasses the Dutch locale validation error entirely. <br> Then refresh your browser.

```bash
https://cyberroom.cyber-secure-te.src.surf-hosted.nl/gl/rooms
```

You should now see a + button. Click it to create your first room, then hit Start to launch the vergadering.

---
### Step 8 — Precompile assets

```bash
docker exec -it greenlight-v3 bundle exec rake assets:precompile
docker compose restart greenlight-v3
```

This step compiles the CSS and JavaScript files needed for the web interface. It takes 1–2 minutes.

### Step 9 — Configure the Nginx proxy with IP restriction

BigBlueButton's nginx serves as the reverse proxy. Create a new config file for Greenlight:

```bash
sudo nano /etc/bigbluebutton/nginx/greenlight-v3.nginx
```

Paste the following, replacing the `allow` lines with your own trusted IP addresses or subnets:

```nginx

    
location /gl/signup {
    # ── Block direct access to signup page
    return 403;
    }
    # ──────────────────────────────────────────────────────────

location /gl {
    # ── IP allowlist ──────────────────────────────────────────
    # Only allow access from trusted IP addresses.
    # Use single IPs or CIDR notation (e.g. 192.168.1.0/24).

    allow 77.173.131.0/24;   # example: office/home subnet
    allow 145.38.x.x;        # example: another trusted IP
    deny  all;               # block everyone else
    # ──────────────────────────────────────────────────────────


    # ── DISABLE self-registration via .env file ───────────────
    # If you want the login page to remain publicly reachable 
    # but prevent visitors from creating their own accounts
    # add the line below in .env file
    # ALLOW_GREENLIGHT_ACCOUNTS=false
    # ──────────────────────────────────────────────────────────

    proxy_pass          http://127.0.0.1:5050;
    proxy_set_header    Host              $host;
    proxy_set_header    X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header    X-Forwarded-Proto https;
    proxy_set_header    X-Forwarded-Ssl   on;
    proxy_http_version  1.1;
    proxy_set_header    Upgrade           $http_upgrade;
    proxy_set_header    Connection        "upgrade";
}
```



Test and reload nginx:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

> **Tip — find your current public IP:**
> ```bash
> curl https://api.ipify.org
> ```
> Add that IP to the allowlist before saving. For campus users, ask your IT department for the institutional CIDR block.

> **Alternative — disable self-registration only:**  
> If you want the login page to remain publicly reachable but prevent visitors from creating their own accounts, set the following in `~/greenlight/.env` instead of using IP restrictions:
> ```
> ALLOW_GREENLIGHT_ACCOUNTS=false
> ```
> Then restart Greenlight: `docker compose restart greenlight-v3`


> **Dynamic IP?** If your home or office IP changes regularly, whitelist your ISP's subnet
> (e.g. `77.173.131.0/24`) instead of a single address, or ask your ISP for a static IP.
> For campus deployments, ask your IT department for the institutional CIDR block.

**Alternative — disable self-registration only:**
> If you want the login page to remain publicly reachable but prevent visitors from
> creating their own accounts, set the following in `~/greenlight/.env` instead:
> ```
> ALLOW_GREENLIGHT_ACCOUNTS=false
> ```
> Then restart Greenlight: `docker compose restart greenlight-v3`

---

## Part 3: Log In and Verify

Open your browser and navigate to:

```
https://yourdomain.example.nl/gl
```

Log in with the email and password you set in Step 7 of Part 2.

After logging in, verify everything works:

1. Go to **Admin Panel** (top-right menu)
2. Check that your BBB server appears under **Server Rooms**
3. Create a test room and click **Start** to launch a meeting

---

## Troubleshooting

### Check container logs

```bash
docker logs greenlight-v3 --tail 50
docker logs postgres --tail 20
```

### Restart everything cleanly

```bash
cd ~/greenlight
docker compose down && docker compose up -d
sleep 15
```

### Check BBB server health

```bash
sudo bbb-conf --check
sudo bbb-conf --status
```

### Reset the admin password

```bash
docker exec -it greenlight-v3 bundle exec rails console
```

```ruby
u = User.find_by(email: 'admin@yourdomain.nl')
u.update!(password: 'NewPassword123!', password_confirmation: 'NewPassword123!')
exit
```

### ERR_TOO_MANY_REDIRECTS

This means Rails is forcing an HTTP→HTTPS redirect loop. Ensure the nginx config uses `X-Forwarded-Proto https` (hardcoded, not `$scheme`) and that `FORCE_SSL=false` is set in both `.env` and `docker-compose.yml`.

### HTTP 500 / asset pipeline error

Run the asset precompile step again:

```bash
docker exec -it greenlight-v3 bundle exec rake assets:precompile
docker compose restart greenlight-v3
```

### "Fout" error / infinite loading

The database data migrations did not complete. Run:

```bash
docker exec -it greenlight-v3 bundle exec rake data:migrate
docker compose restart greenlight-v3
```

---

## Security Notes

- Change the default admin password immediately after first login
- Keep `SECRET_KEY_BASE` secret — it signs all user sessions
- Rotate your BBB API secret periodically: `sudo bbb-conf --secret`
- Never commit your `.env` file to version control — add it to `.gitignore`
- Restrict SSH access to known IP ranges in your firewall rules

---