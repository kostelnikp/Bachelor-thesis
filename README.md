# Bachelor Project – SDRTrunk + Django Server

This project is designed to process data captured using the **SDRTrunk** application and then handle it via a **Django server** running on **Daphne**.

---

##  Features

-  **Real-time DMR Data Processing** – receives and processes DMR communication directly from SDRTrunk.  
-  **Database Storage** – all captured communication is validated, transformed, and stored for further analysis.  
-  **Statistics Dashboard** – interactive charts (powered by Highcharts) showing distribution of communication types and frequencies.  
-  **Map Visualization** – events with GPS data are displayed on an interactive map (Leaflet.js), with detailed info on click.  
-  **History View** – full event log with filtering, sorting, and search (DataTables integration).  
-  **Record Management** – option to delete unnecessary or invalid records.  
-  **Frequency Configuration** – manage and configure monitored frequencies via the web interface.  
-  **Headless Mode Integration** – full compatibility with SDRTrunk running in headless mode.  
-  **Unknown Packet Handling** – ability to capture, decode, and analyze raw/unknown DMR packets (e.g., GPS data in GPRMC format).  

---

## Hardware Requirements

- **RTL-SDR receiver**
- **Antenna**

*Without a properly connected RTL-SDR receiver and antenna, no data can be captured.*

---

## Software Requirements

- **Python 3.10+**
- **pip** (Python package manager)
- **Java Runtime Environment** (for SDRTrunk)
- **RTL-SDR drivers** (installed via Zadig)
- **Daphne** (included in requirements)

---

## Installation

### 1. Installing RTL-SDR drivers

- Download the **Zadig** application: [https://zadig.akeo.ie/](https://zadig.akeo.ie/)  
- Plug in the RTL-SDR receiver.  
- In Zadig, select the device **Bulk-In, Interface 0**.  
- Click **Install Driver** (WinUSB).  

### 2. Setting up the Python server

1. Clone or download this project:

    ```bash
    cd WebSocketServer
    ```

2. Create a virtual environment:

    ```bash
    python -m venv venv
    venv\Scripts\activate     # Windows
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Run the server with Daphne:

    ```bash
    daphne -b 127.0.0.1 -p 8000 dmrserver.asgi:application
    ```

---

## Usage

- Make sure your RTL-SDR receiver and antenna are properly connected.

### SDRTrunk Setup

- **On the first run of SDRTrunk**, you need to manually configure in the GUI:
  - Create your own **playlists** with the configured signal source (e.g., frequency, modulation type).
  - Playlists must be active in order for SDRTrunk to process the received data.
  - In the **Playlist Manager**, you must create an **empty playlist** named **`monitored`**.
    - This playlist is required for proper channel management.
    - Without it, the application will not correctly process the data streams.

- **Note:** In **headless mode** (without GUI), it is not possible to create playlists.  
  Therefore, they must be configured in GUI mode before using headless mode.

---

- Once the server is running, data will be sent via WebSocket to the Django server.  
- The Django server will process the data in real time.  
- Everything runs locally on `127.0.0.1:8000`.  

---

## Screenshots

### Homepage
![Homepage](/Screenshots/Homepage.jpg?raw=true "Homepage")

### History
![Employees](/Screenshots/History.jpg?raw=true "Exercise")

### Map
![Workout](/Screenshots/Map.jpg?raw=true "Workout")

### Statistics
![Workout](/Screenshots/Statistics.jpg?raw=true "Workout")
