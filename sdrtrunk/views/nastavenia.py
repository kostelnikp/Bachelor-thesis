import os
import platform
import subprocess
import xml.etree.ElementTree as ET

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
TARGET_XML_PATH = 'monitored_channels.xml'


def nastavenia(request):
    return render(request, 'nastavenia.html')


@csrf_exempt
def add_monitored_channel(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            frequency_input = data.get('frequency')
            if not frequency_input:
                return JsonResponse({'error': 'Nebola zadaná hodnota frekvencie.'}, status=400)

            # Konverzia frekvencie z MHz na Hz:
            try:
                frequency_mhz = float(frequency_input)
                frequency_hz = int(round(frequency_mhz * 1_000_000))
                frequency_str = f"{frequency_hz:09d}"
            except Exception as conv_err:
                return JsonResponse({'error': f'Chyba pri konverzii frekvencie: {str(conv_err)}'}, status=400)

            if not os.path.exists(XML_FILE_PATH):
                return JsonResponse({'error': 'Zdrojový XML súbor neexistuje.'}, status=400)

            source_tree = ET.parse(XML_FILE_PATH)
            source_root = source_tree.getroot()

            matched_channel = None
            for channel in source_root.findall('channel'):
                source_conf = channel.find('source_configuration')
                if source_conf is not None and source_conf.attrib.get('frequency') == frequency_str:
                    matched_channel = channel
                    break
            if matched_channel is None:
                return JsonResponse({'error': 'Kanál s danou frekvenciou sa nenašiel v zdrojovom XML.'}, status=404)

            new_channel = ET.Element('channel')
            for attr, value in matched_channel.attrib.items():
                if attr not in ['name', 'system', 'site']:
                    new_channel.set(attr, value)
            new_channel.set('enabled', 'true')

            for child in matched_channel:
                if child.tag == 'alias_list_name':
                    continue
                child_copy = ET.fromstring(ET.tostring(child, encoding='utf-8'))
                new_channel.append(child_copy)

            if os.path.exists(TARGET_XML_PATH):
                target_tree = ET.parse(TARGET_XML_PATH)
                target_root = target_tree.getroot()
            else:
                target_root = ET.Element('playlist', attrib={'version': '1.0'})
                target_tree = ET.ElementTree(target_root)

            for channel in target_root.findall('channel'):
                src_conf = channel.find('source_configuration')
                if src_conf is not None and src_conf.attrib.get('frequency') == frequency_str:
                    return JsonResponse({'message': 'Tento kanál je už monitorovaný.'})

            target_root.append(new_channel)
            target_tree.write(TARGET_XML_PATH, encoding='utf-8', xml_declaration=True)

            return JsonResponse({'message': 'Kanál bol úspešne pridaný do monitorovaných.'})
        except Exception as e:
            return JsonResponse({'error': f'Chyba pri spracovaní: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'Nepovolená metóda.'}, status=405)


@csrf_exempt
def remove_monitored_channel(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            frequency_input = data.get('frequency')
            if not frequency_input:
                return JsonResponse({'error': 'Nebola zadaná hodnota frekvencie.'}, status=400)

            # Konverzia frekvencie z MHz na Hz:
            try:
                frequency_mhz = float(frequency_input)
                frequency_hz = int(round(frequency_mhz * 1_000_000))
                frequency_str = f"{frequency_hz:09d}"
            except Exception as conv_err:
                return JsonResponse({'error': f'Chyba pri konverzii frekvencie: {str(conv_err)}'}, status=400)

            if not os.path.exists(TARGET_XML_PATH):
                return JsonResponse({'error': 'Cieľový XML súbor neexistuje.'}, status=400)

            target_tree = ET.parse(TARGET_XML_PATH)
            target_root = target_tree.getroot()

            removed = False
            for channel in list(target_root.findall('channel')):
                src_conf = channel.find('source_configuration')
                if src_conf is not None and src_conf.attrib.get('frequency') == frequency_str:
                    target_root.remove(channel)
                    removed = True
                    break

            if not removed:
                return JsonResponse({'error': 'Frekvencia nebola nájdená v monitorovaných kanáloch.'}, status=404)

            target_tree.write(TARGET_XML_PATH, encoding='utf-8', xml_declaration=True)

            return JsonResponse({'message': 'Kanál bol úspešne odstránený z monitorovaných.'})
        except Exception as e:
            return JsonResponse({'error': f'Chyba pri spracovaní: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'Nepovolená metóda.'}, status=405)


def load_frequencies(request):
    try:
        if not XML_FILE_PATH:
            return JsonResponse({'error': 'XML cesta nebola nájdená'}, status=404)

        tree = ET.parse(XML_FILE_PATH)
        root = tree.getroot()

        response = get_selected_frequencies(request)
        frequencies = json.loads(response.content).get('frequencies')
        if frequencies:
            center_frequency = float(frequencies[0])
        else:
            center_frequency = None

        if center_frequency:
            sample_rate = float(config.get('SAMPLE_RATE'))
            min_frequency = center_frequency - sample_rate / 2
            max_frequency = center_frequency + sample_rate / 2




        channels = []
        for channel in root.findall('channel'):
            name = channel.get('name')
            frequency = channel.find('.//source_configuration').get('frequency')
            formatted_frequency = f'{int(frequency) / 1000000:.4f} MHz'

            if center_frequency:
                valid = min_frequency <= float(formatted_frequency.split()[0]) <= max_frequency
            else:
                valid = True
            channels.append({
                'name': name,
                'frequency': formatted_frequency,
                'valid': valid
            })

        return JsonResponse({'data': channels})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def load_playlist_files(request):
    """
    Prejde adresár SDRTrunk/playlist umiestnený v domovskom adresári používateľa
    a vráti zoznam názvov XML súborov (playlistov) vo formáte JSON pre DataTables.
    """
    try:
        playlist_dir = os.path.join(os.path.expanduser("~"), "SDRTrunk", "playlist")

        if not os.path.isdir(playlist_dir):
            return JsonResponse({'error': 'Cieľový adresár neexistuje.'}, status=404)

        files = []
        for file in os.listdir(playlist_dir):
            if file.lower().endswith('.xml'):
                files.append({'file_name': file, 'file_path': os.path.join(playlist_dir, file)})

        return JsonResponse({'data': files})
    except Exception as e:
        return JsonResponse({'error': f"Chyba pri načítaní súborov: {str(e)}"}, status=500)


@csrf_exempt
def select_xml(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_xml_path = data.get("file_path")

            if new_xml_path and new_xml_path.endswith(".xml"):
                global XML_FILE_PATH
                XML_FILE_PATH = new_xml_path
                config['XML_FILE_PATH'] = new_xml_path
                save_config(config)
                return JsonResponse({"message": "XML súbor bol úspešne vybraný."})
            else:
                return JsonResponse({"error": "XML súbor sa nepodarilo vybrať."}, status=400)

        except Exception as e:
            return JsonResponse({"error": "Pri požiadavke nastala chyba."}, status=400)

@csrf_exempt
def get_selected_playlist(request):
    global XML_FILE_PATH
    if XML_FILE_PATH:
        return JsonResponse({"selected_playlist_path": XML_FILE_PATH})
    return JsonResponse({"error": "Žiadny vybraný playlist"}, status=404)

@csrf_exempt
def get_selected_frequencies(request):
    global TARGET_XML_PATH
    if TARGET_XML_PATH:
        try:
            tree = ET.parse(TARGET_XML_PATH)
            root = tree.getroot()

            frequencies = []
            for channel in root.findall('channel'):
                source_conf = channel.find('source_configuration')
                if source_conf is not None:
                    frequency = source_conf.attrib.get('frequency')
                    if frequency:
                        frequencyMHz = f"{int(frequency) / 1000000:.4f}"
                        frequencies.append(frequencyMHz)

            return JsonResponse({'frequencies': frequencies})

        except Exception as e:
            return JsonResponse({'error': f'Nepodarilo sa získať frekvencie: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'Cesta ku XML nie je platná'}, status=404)




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
