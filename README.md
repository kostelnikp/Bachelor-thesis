# Bakalársky projekt – SDRTrunk + Django Server

Tento projekt slúži na spracovanie dát zachytených pomocou SDRTrunk aplikácie a ich následné spracovanie cez Django server bežiaci cez Daphne.

---

## Hardvérové požiadavky

- **RTL-SDR prijímač**
- **Anténa**

*Bez správneho pripojenia RTL-SDR prijímača a antény nebude možné zachytávať žiadne dáta.*

---

## Softvérové požiadavky

- **Python 3.10+**
- **pip** (package manager pre Python)
- **Java Runtime Environment** (pre SDRTrunk)
- **RTL-SDR ovládače** (nainštalované cez Zadig)
- **Daphne** (súčasť requirements)

---

## Inštalácia

### 1. Inštalácia RTL-SDR ovládačov

- Stiahni aplikáciu **Zadig**: [https://zadig.akeo.ie/](https://zadig.akeo.ie/)
- Pripoj RTL-SDR prijímač.
- V Zadigu vyber zariadenie **Bulk-In, Interface 0**.
- Klikni na **Install Driver** (WinUSB).

### 2. Nastavenie Python servera

1. Klonuj alebo stiahni tento projekt:

    ```bash
    cd WebSocketServer
    ```

2. Vytvor virtuálne prostredie:

    ```bash
    python -m venv venv
    venv\Scripts\activate     # Windows
    ```

3. Inštaluj závislosti:

    ```bash
    pip install -r requirements.txt
    ```

4. Spusti server pomocou Daphne:

    ```bash
    daphne -b 127.0.0.1 -p 8000 dmrserver.asgi:application
    ```

---

## Používanie

- Uisti sa, že máš správne pripojený RTL-SDR prijímač a anténu.

### Nastavenie SDRTrunk

- **Pri prvom spustení SDRTrunk** je potrebné manuálne v grafickom rozhraní:
  - Vytvoriť vlastné **playlisty** s nastaveným zdrojom signálu (napr. frekvencia, typ modulácie).
  - Playlisty musia byť aktívne, aby SDRTrunk spracovával prijímané dáta.
  - **V Playlist Manageri** musí byť vytvorený **prázdny playlist** s názvom **`monitored`**.
    - Tento playlist je potrebný pre správne fungovanie správy kanálov.
    - Bez neho nebude aplikácia správne spracovávať dátové streamy.

- **Poznámka:** V **headless režime** (bez GUI) nie je možné playlisty vytvárať. Preto je nutné ich nastaviť v grafickom režime pred použitím headless režimu.


    

- Po spustení servera budú dáta odosielané cez websocket na Django server.
- Django server ich spracuje v reálnom čase.
- Všetko beží lokálne na `127.0.0.1:8000`.

---
