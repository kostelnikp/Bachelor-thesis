import os
import xml.etree.ElementTree as ET
import platform
import subprocess


from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from plotly.io._orca import psutil
from rest_framework.utils import json

CONFIG_FILE = "config.json"

def load_config():
    with open(CONFIG_FILE, "r") as file:
        return json.load(file)


def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)


config = load_config()
XML_FILE_PATH = config.get('XML_FILE_PATH')
SDRTRUNK_PATH = config.get('SDRTRUNK_PATH')


def nastavenia(request):
    return render(request, 'nastavenia.html')

def get_xml_path(request):
    if XML_FILE_PATH:
        return JsonResponse({"xml_path": XML_FILE_PATH})
    return JsonResponse({"error": "XML cesta nebola nájdená"}, status=404)


@csrf_exempt
def update_xml_path(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_xml_path = data.get("xml_path")

            if new_xml_path and new_xml_path.endswith(".xml") and os.path.isfile(new_xml_path):
                global XML_FILE_PATH
                XML_FILE_PATH = new_xml_path
                config['XML_FILE_PATH'] = new_xml_path
                save_config(config)
                return JsonResponse({"message": "XML cesta bola úspešne aktualizovaná"})
            else:
                return JsonResponse({"error": "XML cesta je neplatná"}, status=400)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Nepodporovaná metóda"}, status=405)


def get_bat_path(request):
    if SDRTRUNK_PATH:
        return JsonResponse({"bat_path": SDRTRUNK_PATH})
    return JsonResponse({"error": "Bat cesta nebola nájdená"}, status=404)


@csrf_exempt
def update_bat_path(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_bat_path = data.get("bat_path")

            if new_bat_path and new_bat_path.lower().endswith(".bat") and os.path.isfile(new_bat_path):
                global SDRTRUNK_PATH
                SDRTRUNK_PATH = new_bat_path
                config['SDRTRUNK_PATH'] = new_bat_path
                save_config(config)
                return JsonResponse({"message": "Bat cesta bola úspešne aktualizovaná"})
            else:
                return JsonResponse({"error": "Bat cesta je neplatná"}, status=400)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Nepodporovaná metóda"}, status=405)





def get_monitored_frequency(request):
    """Načíta monitorovanú frekvenciu zo súboru XML"""
    if not os.path.exists(XML_FILE_PATH):
        return JsonResponse({"error": "Súbor nenájdený"}, status=404)

    tree = ET.parse(XML_FILE_PATH)
    root = tree.getroot()

    frequency_node = root.find(".//source_configuration")
    if frequency_node is not None and "frequency" in frequency_node.attrib:
        frequency = int(frequency_node.attrib["frequency"]) / 1_000_000
        return JsonResponse({"monitored_frequency": f"{frequency:.4f} MHz"})

    return JsonResponse({"error": "Frekvencia nebola nájdená"}, status=404)


@csrf_exempt
def update_monitored_frequency(request):
    """Uloží novú monitorovanú frekvenciu do súboru XML"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_frequency = float(data.get("frequency")) * 1_000_000

            tree = ET.parse(XML_FILE_PATH)
            root = tree.getroot()

            frequency_node = root.find(".//source_configuration")
            if frequency_node is not None:
                frequency_node.set("frequency", str(int(new_frequency)))
                tree.write(XML_FILE_PATH, encoding="utf-8", xml_declaration=True)

                return JsonResponse({"message": "Frekvencia bola aktualizovaná"})
            else:
                return JsonResponse({"error": "Nepodarilo sa nájsť uzol frekvencie"}, status=400)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Nepodporovaná metóda"}, status=405)


terminal_process = None


@csrf_exempt
def start_restart_sdrtrunk(request):
    global terminal_process

    if request.method == "GET":
        try:
            for process in psutil.process_iter(attrs=['pid', 'name']):
                if "java" in process.info['name'].lower():
                    process.terminate()

            if terminal_process and terminal_process.poll() is None:
                terminal_process.terminate()

            if platform.system() == "Windows":
                terminal_process = subprocess.Popen(["cmd.exe", "/c", f"start cmd /c {SDRTRUNK_PATH}"], shell=True)
            else:
                terminal_process = subprocess.Popen(["gnome-terminal", "--", "bash", "-c", f"{SDRTRUNK_PATH}"])

            return JsonResponse({"message": "SDRTrunk bol úspešne reštartovaný v novom termináli."})

        except Exception:
            return JsonResponse({"error": "Nepodarilo sa reštartovať SDRTrunk."}, status=500)

    return JsonResponse({"error": "Nepodporovaná metóda"}, status=405)



