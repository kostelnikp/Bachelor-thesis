# sdrtrunk/consumers.py

import re
from datetime import datetime

from channels.generic.websocket import WebsocketConsumer


class SDRTrunkConsumer(WebsocketConsumer):
    def connect(self):
        print("Client connected")
        self.accept()

    def disconnect(self, close_code):
        print("Client diconnected")
        pass

    def parse_data(self, text_data):
        event_match = re.search(r'DMR DECODE EVENT:\s+([A-Za-z\s]+)\s', text_data)
        if not event_match:
            raise ValueError("Event type not found in data")
        event_type = event_match.group(1).strip()

        if not event_type:
            raise ValueError("Parsed event is empty or None")

        # GROUP CALL
        GROUP_CALL_REGEX = re.compile(
            r'TIMESTAMP:\s+(?P<timestamp>.*?)\s+'
            r'FREQUENCY:\s+(?P<frequency>[\d\.]+)\s+'
            r'DMR DECODE EVENT:\s+Group Call\s+'
            r'(?:DETAILS:\s*(?P<details>.*?)\s+)?'
            r'IDS:(?P<ids>.*?)\s+'
            r'DURATION:(?P<duration>\d+)\s+'
            r'(?:CHANNEL:\s*(?P<channel>\w+(?:\s+[\d\.]+)?)\s+)?'
            r'TIMESLOT:(?P<timeslot>\d+)\s+'
            r'EVENT\s+ID:\s+(?P<event_id>\d+)'
        )

        # SMS
        SMS_REGEX = re.compile(
            r'TIMESTAMP:\s+(?P<timestamp>.*?)\s+'
            r'FREQUENCY:\s+(?P<frequency>[\d\.]+)\s+'
            r'DMR DECODE EVENT:\s+SMS\s+'
            r'DETAILS:MESSAGE:\s*(?P<details>.*?)\s+'
            r'IDS:(?P<ids>.*?)\s+'
            r'DURATION:(?P<duration>\d+)\s+'
            r'(?:CHANNEL:\s*(?P<channel>\w+(?:\s+[\d\.]+)?)\s+)?'
            r'TIMESLOT:(?P<timeslot>\d+)\s+'
            r'EVENT\s+ID:\s+(?P<event_id>\d+)'
        )

        # DATA PACKET
        DATA_PACKET_REGEX = re.compile(
            r'TIMESTAMP:\s+(?P<timestamp>.*?)\s+'
            r'FREQUENCY:\s+(?P<frequency>[\d\.]+)\s+'
            r'DMR DECODE EVENT:\s+Data Packet\s+'
            r'(?:DETAILS:\s*(?P<details>.*?)\s+)?'
            r'IDS:(?P<ids>.*?)\s+'
            r'DURATION:(?P<duration>\d+)\s+'
            r'(?:CHANNEL:\s*(?P<channel>\w+(?:\s+[\d\.]+)?)\s+)?'
            r'TIMESLOT:(?P<timeslot>\d+)\s+'
            r'EVENT\s+ID:\s+(?P<event_id>\d+)'
        )

        # GPS
        GPS_REGEX = re.compile(
            r'TIMESTAMP:\s+(?P<timestamp>.*?)\s+'
            r'FREQUENCY:\s+(?P<frequency>[\d\.]+)\s+'
            r'DMR DECODE EVENT:\s+GPS\s+'
            r'IDS:\s*(?P<ids>.*?)\s+'
            r'(?:CHANNEL:\s*(?P<channel>[\w\s\.]+)\s+)?' 
            r'DETAILS:\s*(?:LOCATION:)?\s*(?P<latitude>[\d\.,]+[NS])\s+(?P<longitude>[\d\.,]+[EW])\s+'
            r'EVENT\s+ID:\s+(?P<event_id>\d+)'
        )

        if event_type == "Group Call":
            pattern = GROUP_CALL_REGEX
        elif event_type == "SMS":
            pattern = SMS_REGEX
        elif event_type == "Data Packet":
            pattern = DATA_PACKET_REGEX
        elif event_type == "GPS":
            pattern = GPS_REGEX
        else:
            raise ValueError(f"Neznámy event type: {event_type}")

        match = pattern.search(text_data)
        if not match:
            raise ValueError(f"Nepodarilo sa parseovať data z reťazca: {text_data}")

        data = match.groupdict()

        # Uloženie eventu do parsed_data, aby bol dostupný pre databázu
        data["event"] = event_type

        # Konverzia údajov
        data["timestamp"] = datetime.strptime(data["timestamp"], "%a %b %d %H:%M:%S CET %Y")
        data["duration"] = int(data["duration"]) / 1000 if "duration" in data else None  # Premena na sekundy
        data["frequency"] = float(data["frequency"])
        data["event_id"] = int(data["event_id"])
        if "timeslot" in data and data["timeslot"]:
            data["timeslot"] = int(data["timeslot"])
        else:
            data["timeslot"] = None

        # Spracovanie CHANNEL
        if data["channel"]:
            channel_parts = data["channel"].split()
            try:
                data["channel_number"] = int(channel_parts[0]) if channel_parts[0].isdigit() else None
            except ValueError:
                data["channel_number"] = None
        else:
            data["channel_number"] = None

        # Spracovanie IDS (odstránenie "DMR" a správne rozdelenie)
        ids_parts = [part.strip() for part in data["ids"].split(",") if part.strip() != "DMR"]

        ids_numbers = []
        ids_aliases = []

        for part in ids_parts:
            if part.isdigit():
                ids_numbers.append(part)
            else:
                ids_aliases.append(part)

        data["ids_numbers"] = ids_numbers
        data["ids_aliases"] = [" ".join(ids_aliases)] if ids_aliases else []

        if event_type == "SMS" and len(ids_numbers) >= 2:
            data["source"] = ids_numbers[1]  # Prvé ID je zdroj
            data["destination"] = ids_numbers[0]  # Druhé ID je cieľ
        elif event_type == "Group Call" and len(ids_numbers) >= 2:
            data["destination"] = ids_numbers[1]  # Prvý číselný ID po odstránení "DMR" je cieľ
            data["source"] = ",".join(ids_numbers[2:] + data["ids_aliases"]) if len(ids_numbers) > 2 else None
        elif event_type == "Data Packet" and len(ids_numbers) >= 2:
            data["source"] = ids_numbers[0]
            data["destination"] = ids_numbers[1]
        elif event_type == "GPS":
            def convert_gps(coord):
                coord = coord.strip()
                direction = coord[-1]
                value = coord[:-1].replace(",", ".")

                try:
                    decimal_value = float(value)
                    if direction in ["S", "W"]:
                        decimal_value *= -1

                    return decimal_value
                except ValueError:
                    raise ValueError(f"⚠️ Chyba pri konverzii GPS súradnice: {coord}")

            data["latitude"] = convert_gps(data["latitude"])
            data["longitude"] = convert_gps(data["longitude"])
        else:
            data["destination"] = None
            data["source"] = None

        return data

    def receive(self, text_data):
        print("Received data:", text_data)
        from sdrtrunk.models import DMRData, GPSData

        try:
            parsed_data = self.parse_data(text_data)

            if not parsed_data.get("event"):
                raise ValueError("Event cannot be NULL!")



            if parsed_data.get("event") == "GPS":
                gps_id = parsed_data.get("ids_numbers")[0] if parsed_data.get("ids_numbers") else None

                if gps_id:
                    dmr_instance = DMRData.objects.filter(source=gps_id).last()

                    if not dmr_instance:
                        dmr_instance = DMRData.objects.filter(destination=gps_id).last()

                    if dmr_instance:

                        GPSData.objects.create(
                            dmr_data=dmr_instance,
                            latitude=parsed_data.get("latitude"),
                            longitude=parsed_data.get("longitude")
                        )
                    else:
                        print(f"⚠️ GPS event {gps_id} nemá priradený DMR event!")
                        print("📌 Všetky DMR eventy v databáze:")
                        for dmr in DMRData.objects.all():
                            print(f" - ID: {dmr.id}, Source: {dmr.source}, Destination: {dmr.destination}")

            else:
                DMRData.objects.create(
                    timestamp=parsed_data.get("timestamp"),
                    duration_s=parsed_data.get("duration"),
                    protocol="DMR",
                    event=parsed_data.get("event"),
                    source=parsed_data.get("source"),
                    destination=parsed_data.get("destination"),
                    channel_number=parsed_data.get("channel_number"),
                    frequency=parsed_data.get("frequency"),
                    timeslot=parsed_data.get("timeslot"),
                    color_code=parsed_data.get("color_code"),
                    details=parsed_data.get("details"),
                    event_id=parsed_data.get("event_id")
                )

        except Exception as e:
            print("Error saving data:", e)


