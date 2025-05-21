<div align="center">

<picture>
  <img alt="tiny corp logo" src="https://raw.githubusercontent.com/kiuX89/IP-exporter/refs/heads/main/ip-exporter.png" width="50%" height="50%">
</picture>

IP Exporter is an exporter that checks whether public IP addresses respond to ping or fail.
</div>

---

## Installation

Clone the repository and fill in the ip.conf file with a name, an IP address, and geographic coordinates.
You can add as many IP addresses to monitor as you want. This tool requires InfluxDB and Pushgateway to work.
Update the host, port, username, and password variables for InfluxDB, and set localhost:9091 for Pushgateway.

## Warning

This project may be updated during my free time. It addresses a personal need and works as intended.
Feel free to contribute or fork it.