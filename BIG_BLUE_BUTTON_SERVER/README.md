# BBB+Greenlightv3_installatie_JULI_2026.md

Dit document beschrijft de volledige technische handleiding, het geautomatiseerde deploymentscript en de nabeveiligingsstappen voor een productie-waardige **BigBlueButton 3.0** en **Greenlight v3** omgeving, uitgevoerd in juli 2026 op de **SURF HPC Cloud**.

---

## 1. Infrastructuur & Cloud Specificaties

De virtuele machine is ingericht binnen de SURF HPC Cloud omgeving onder de volgende specificaties (afgeleid van de deployment configuratie):

| Component | Waarde / Specificatie |
| :--- | :--- |
| **Cloud Provider** | SURF HPC Cloud |
| **Catalogus Item** | Docker Compose Langflow TINY |
| **Besturingssysteem** | Ubuntu 22.04.5 LTS (Jammy Jellyfish) |
| **Hardware Resources** | 8 CPU Cores, 64 GB RAM |
| **IP-adres (IPv4)** | `145.38.205.177` |
| **Fully Qualified Domain Name (FQDN)** | `greenroom.cyber-secure-te.src.surf-hosted.nl` |
| **E-mailbeheerder** | `aihubpilot@hr.nl` |
| **Collaboratie / Wallet** | `cyber-secure-tele-intervw-hr` |

---

## 2. Netwerk & Security Groups

De firewall en security groups van de instance zijn geconfigureerd met de volgende poorttoewijzingen:

| Van Poort | Naar Poort | Protocol | Verkeer (Traffic) | Doel / Functie |
| :---: | :---: | :---: | :---: | :--- |
| 22 | 22 | tcp | in | SSH Remote Beheer |
| 80 | 80 | tcp | in | HTTP / Let's Encrypt Validatie |
| 443 | 443 | tcp | in | HTTPS (Secure BigBlueButton & Greenlight v3) |
| 3389 | 3389 | tcp | in | Remote Desktop / Beheer |
| 7860 | 7860 | tcp | in | Langflow / UI Services |
| 8080 | 8080 | tcp | in | Container Services / Proxy |
| 1 | 65535 | udp | out | Uitgaand UDP-verkeer (TURN/STUN & media streams) |
| 1 | 65535 | tcp | out | Uitgaand TCP-verkeer |

---

## 3. Automatisch Installatiescript (`create_BBB+greenlightv3.sh`)

In plaats van handmatige stappen is het gehele deploymentproces geautomatiseerd middels het volgende bash-script:

```bash
#!/bin/bash
# ==============================================================================
# Script Name: create_BBB+greenlightv3.sh
# Description: Automated installation of BigBlueButton 3.0 and Greenlight v3 
#              on Ubuntu 22.04 (jammy) server with automated admin provisioning.
# ==============================================================================

set -eo pipefail

# Configuration Variables
HOSTNAME="${BBB_HOSTNAME:-greenroom.cyber-secure-te.src.surf-hosted.nl}"
EMAIL="${BBB_EMAIL:-aihubpilot@hr.nl}"
BBB_VERSION="${BBB_VERSION:-jammy-300}"

# Default Administrator Credentials
ADMIN_NAME="${ADMIN_NAME:-Administrator}"
ADMIN_EMAIL="${ADMIN_EMAIL:-aihubpilot@hr.nl}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-Eb462902-e974-4113-a873-947aa360fcec!}"

# Ensure script is run with root privileges
if [ "$EUID" -ne 0 ]; then
  echo "[-] Please run this script with sudo or as root: sudo ./create_BBB+greenlightv3.sh"
  exit 1
fi

echo "[+] Starting BigBlueButton 3.0 + Greenlight v3 deployment..."
echo "[+] Hostname: $HOSTNAME"
echo "[+] Email:    $EMAIL"
echo "[+] Version:  $BBB_VERSION"

# Run official BigBlueButton 3.0 installer with jammy-300, firewall (-w), and Greenlight v3 (-g)
wget -qO- https://raw.githubusercontent.com/bigbluebutton/bbb-install/v3.0.x-release/bbb-install.sh | bash -s -- \
  -v "$BBB_VERSION" \
  -s "$HOSTNAME" \
  -e "$EMAIL" \
  -w \
  -g

echo "[+] Installation finished. Checking Greenlight v3 deployment directory..."

# Validate directory existence
GREENLIGHT_DIR="/root/greenlight-v3"
if [ ! -d "$GREENLIGHT_DIR" ]; then
  echo "[-] Error: Expected directory $GREENLIGHT_DIR was not created by the installer."
  exit 1
fi

cd "$GREENLIGHT_DIR"

echo "[+] Waiting for greenlight-v3 container to boot up..."
until sudo docker compose ps --status running | grep -q "greenlight-v3"; do
  sleep 5
done

# Give Rails database connections time to settle
sleep 10

echo "[+] Greenlight v3 is running. Generating administrator account..."

# Create the admin user non-interactively
sudo docker compose exec -T greenlight-v3 bundle exec rake "admin:create[$ADMIN_NAME,$ADMIN_EMAIL,$ADMIN_PASSWORD]" || {
  echo "[-] Note: Automatic creation skipped or user already exists."
}

echo "=========================================================================="
echo "[+] Full deployment and configuration completed successfully!"
echo "[+] URL:          https://$HOSTNAME"
echo "[+] Admin Email:  $ADMIN_EMAIL"
echo "[+] Admin Pass:   $ADMIN_PASSWORD"
echo "=========================================================================="
```

---

## 4. Handmatige Correctie & Account Provisioning

Tijdens de live implementatie kon het standaardwachtwoord vanwege complexiteitseisen of Bash-escape tekens specifiek worden ingesteld via de volgende handmatige rake-opdracht:

```bash
sudo docker compose -f /root/greenlight-v3/docker-compose.yml exec greenlight-v3 bundle exec rake 'admin:create[admin,aihubpilot@hr.nl,Eb462902-e974-4113-a873-947aa360fcec!]'
```

**Credentials Resultaat:**
- **Name:** `admin`
- **Email:** `aihubpilot@hr.nl`
- **Password:** `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- **Role:** `Administrator`

---

## 5. Testomgeving en Gebruik (`TESTROOM001`)

Na inloggen op `https://greenroom.cyber-secure-te.src.surf-hosted.nl`, is een testruimte aangemaakt:
- **Room Name:** `TESTROOM001`
- **Join URL:** `https://greenroom.cyber-secure-te.src.surf-hosted.nl/rooms/yf2-map-0gg-frw/join`
- **Features:** Geverifieerd met actieve audio (speaker brug) en video-integratie.

---

## 6. Beveiliging: Blokkeren van Open Registraties (Sign-ups uitschakelen)

Om te voorkomen dat willekeurige gebruikers accounts aanmaken op de server, kan de registratiemethode worden omgezet naar *Invite Only*.

### Methode 1: Via de Rails Console (Aanbevolen)
Voer het volgendecommando uit in de terminal:
```bash
sudo docker compose -f /root/greenlight-v3/docker-compose.yml exec greenlight-v3 bundle exec rails runner '
  setting = Setting.find_by(name: "RegistrationMethod")
  site_setting = SiteSetting.find_by(setting: setting)
  site_setting.update!(value: "invite")
'
```

### Methode 2: Via het Admin Panel
1. Log in op de Greenlight v3 interface met het administratoraccount (`admin`).
2. Klik rechtsboven op je profielmenu en selecteer **Organization**.
3. Navigeer naar **Site Settings**.
4. Wijzig de **Registration Method** in **Invite Only**.
5. Sla de wijzigingen op.
