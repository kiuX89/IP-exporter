from ping3 import ping, verbose_ping
from influxdb import InfluxDBClient
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import time
from datetime import datetime
import json
import pytz

client = InfluxDBClient(host='localhost', port=8086, username='USER', password='PASWSWORD')

client.switch_database('metric')

registry = CollectorRegistry()

metrics = {}

last_values = {}

dispo_service = Gauge('dispo_service', 'Service availability', ['name', 'ip'], registry=registry)

def calculate_ping(ip, count=1):
    failed_pings = 0
    for _ in range(count):
        try:
            delay = ping(ip)
            if delay is None:
                failed_pings += 1
        except Exception as e:
            print(f"Erreur lors du ping de {ip}: {e}")
            failed_pings += 1
    loss = round((failed_pings / count) * 100)
    return loss

def delete_ip_data(ip):
    try:
        client.query(f'DELETE FROM ping_loss WHERE ip = \'{ip}\'')
        print(f"Données supprimées pour l'adresse IP : {ip}")
    except Exception as e:
        print(f"Erreur lors de la suppression des données pour l'adresse IP {ip} : {e}")

def get_existing_ips():
    result = client.query('SHOW TAG VALUES FROM ping_loss WITH KEY = "ip"')
    if result:
        return [item['value'] for item in list(result.get_points())]
    else:
        return []

def get_existing_timestamp(ip):
    result = client.query(f'SELECT last(value) FROM ping_loss WHERE ip = \'{ip}\'')
    if result:
        return list(result.get_points(measurement='ping_loss'))[0]['time']
    else:
        return None

if __name__ == '__main__':
    while True:
        with open('ip.conf', 'r') as f:
            ipes = json.load(f)

        existing_ips = get_existing_ips()
        for ip in existing_ips:
            if ip not in [ip for name, ip, lat, lon in ipes]:
                delete_ip_data(ip)
        for name, ip, lat, lon in ipes:
            timestamp = get_existing_timestamp(ip)
            if timestamp is None:
                paris_tz = pytz.timezone('Europe/Paris')
                timestamp = datetime.now(paris_tz).strftime('%Y-%m-%dT%H:%M:%S%z')
            loss = calculate_ping(ip)
            availability = 100 - loss
            dispo_service.labels(name=name, ip=ip).set(availability)
            json_body = [
                {
                    "measurement": "ping_loss",
                    "tags": {
                        "name": name,
                        "ip": ip,
                    },
                    "fields": {
                        "value": loss,
                        "latitude": lat,
                        "longitude": lon
                    },
                    "time": timestamp
                }
            ]
            print(f"Écriture des données dans InfluxDB : {json_body}")
            try:
                client.write_points(json_body)
            except Exception as e:
                print(f"Erreur lors de l'écriture des données dans InfluxDB : {e}")

            if loss == 100:
                safe_name = name.replace('-', '_')
                metric_name = f'dispo_{safe_name}_down'
                if metric_name not in metrics:
                    metrics[metric_name] = Gauge(metric_name, 'Ping loss percentage', ['name', 'ip'], registry=registry)
                ping_loss = metrics[metric_name]
                if last_values.get(metric_name) != 100:
                    ping_loss.labels(name=name, ip=ip).set(loss)
                    push_to_gateway('localhost:9091', job='dispo_loss', registry=registry)
                last_values[metric_name] = loss

        time.sleep(60)
