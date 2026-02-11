import subprocess
import json
import logging
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timedelta
from flask import Flask, request, Response, jsonify
from urllib.parse import unquote
import os

# Ensure UTF-8 encoding for subprocesses
os.environ['PYTHONIOENCODING'] = 'utf-8'

app = Flask(__name__)

# Set up logging with UTF-8 encoding
logging.basicConfig(level=logging.INFO, encoding='utf-8')

# Directory where .m3u files are stored
M3U_DIR = os.environ.get('M3U_DIR', '/data')

# Host IP/hostname used in .m3u files
HOST_IP = os.environ.get('HOST_IP', '192.168.1.123')
SERVER_PORT = os.environ.get('SERVER_PORT', '6095')

def generate_m3u_from_xml_file(xml_path, output_path):
    """Parse a youtubelinks.xml file and write a youtubelive.m3u playlist."""
    if not os.path.isfile(xml_path):
        logging.warning(f"XML file not found at {xml_path}, skipping m3u generation.")
        return False

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        logging.error(f"Failed to parse XML file {xml_path}: {str(e)}")
        return False

    base_url = f'http://{HOST_IP}:{SERVER_PORT}'
    lines = ['#EXTM3U']
    for idx, channel in enumerate(root.findall('channel'), start=1):
        name = (channel.find('channel-name').text or '').strip() if channel.find('channel-name') is not None else 'Unknown'
        tvg_id = (channel.find('tvg-id').text or '').strip() if channel.find('tvg-id') is not None else ''
        tvg_name = (channel.find('tvg-name').text or '').strip() if channel.find('tvg-name') is not None else name
        tvg_logo = (channel.find('tvg-logo').text or '').strip() if channel.find('tvg-logo') is not None else ''
        group_title = (channel.find('group-title').text or '').strip() if channel.find('group-title') is not None else 'General'
        channel_number = (channel.find('channel-number').text or '').strip() if channel.find('channel-number') is not None else str(idx)
        youtube_url = (channel.find('youtube-url').text or '').strip() if channel.find('youtube-url') is not None else ''

        if not youtube_url:
            logging.warning(f"Skipping channel '{name}' due to missing YouTube URL.")
            continue

        lines.append(
            f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{tvg_name}"'
            f' tvg-chno="{channel_number}" tvg-logo="{tvg_logo}" group-title="{group_title}",{name}'
        )
        lines.append(f'{base_url}/stream?url={youtube_url}')

    content = '\n'.join(lines) + '\n'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    logging.info(f"Generated {output_path} from {xml_path} with {len(lines) - 1} entries.")
    return True

def generate_epg_from_xml_file(xml_path, output_path):
    """Parse a youtubelinks.xml file and generate an XMLTV EPG file."""
    if not os.path.isfile(xml_path):
        logging.warning(f"XML file not found at {xml_path}, skipping EPG generation.")
        return False

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        logging.error(f"Failed to parse XML file {xml_path}: {str(e)}")
        return False

    tv = ET.Element('tv')
    tv.set('generator-info-name', 'youtube-to-m3u')
    tv.set('generator-info-url', f'http://{HOST_IP}:{SERVER_PORT}')

    now = datetime.utcnow()
    channel_count = 0

    for idx, channel in enumerate(root.findall('channel'), start=1):
        tvg_id = (channel.find('tvg-id').text or '').strip() if channel.find('tvg-id') is not None else ''
        tvg_name = (channel.find('tvg-name').text or '').strip() if channel.find('tvg-name') is not None else ''
        name = (channel.find('channel-name').text or '').strip() if channel.find('channel-name') is not None else tvg_name
        tvg_logo = (channel.find('tvg-logo').text or '').strip() if channel.find('tvg-logo') is not None else ''
        channel_number = (channel.find('channel-number').text or '').strip() if channel.find('channel-number') is not None else str(idx)
        youtube_url = (channel.find('youtube-url').text or '').strip() if channel.find('youtube-url') is not None else ''

        if not tvg_id or not youtube_url:
            continue

        # Channel element
        ch_elem = ET.SubElement(tv, 'channel')
        ch_elem.set('id', tvg_id)
        display_name = ET.SubElement(ch_elem, 'display-name')
        display_name.text = tvg_name or name
        chnum_name = ET.SubElement(ch_elem, 'display-name')
        chnum_name.text = channel_number
        if tvg_logo:
            icon = ET.SubElement(ch_elem, 'icon')
            icon.set('src', tvg_logo)

        # Programme element — 24-hour live block repeated for 7 days
        for day_offset in range(7):
            start_time = (now + timedelta(days=day_offset)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(days=1)
            start_str = start_time.strftime('%Y%m%d%H%M%S') + ' +0000'
            end_str = end_time.strftime('%Y%m%d%H%M%S') + ' +0000'

            prog = ET.SubElement(tv, 'programme')
            prog.set('start', start_str)
            prog.set('stop', end_str)
            prog.set('channel', tvg_id)
            title = ET.SubElement(prog, 'title')
            title.set('lang', 'en')
            title.text = f'{tvg_name or name} - Live'
            desc = ET.SubElement(prog, 'desc')
            desc.set('lang', 'en')
            desc.text = f'Live stream from {name}'
            if tvg_logo:
                prog_icon = ET.SubElement(prog, 'icon')
                prog_icon.set('src', tvg_logo)

        channel_count += 1

    # Pretty print the XML
    xml_str = ET.tostring(tv, encoding='unicode', xml_declaration=False)
    xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE tv SYSTEM "xmltv.dtd">\n' + xml_str
    parsed = minidom.parseString(xml_str)
    pretty_xml = parsed.toprettyxml(indent='  ', encoding='UTF-8').decode('utf-8')
    # Remove extra XML declaration added by minidom
    lines = pretty_xml.split('\n')
    if lines[0].startswith('<?xml'):
        lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
    pretty_xml = '\n'.join(lines)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    logging.info(f"Generated EPG {output_path} from {xml_path} with {channel_count} channels.")
    return True

@app.route('/m3u/<path:filename>', methods=['GET'])
def serve_m3u(filename):
    """Serve .m3u files from the configured directory, replacing {{HOST_IP}} and {{PORT}} placeholders."""
    if not filename.endswith('.m3u'):
        return jsonify({'error': 'Only .m3u files can be served'}), 400
    filepath = os.path.join(M3U_DIR, filename)
    if not os.path.isfile(filepath):
        return jsonify({'error': 'File not found'}), 404
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace('{{HOST_IP}}', HOST_IP)
    content = content.replace('{{PORT}}', SERVER_PORT)
    return Response(content, content_type='audio/x-mpegurl')

@app.route('/xml/<path:filename>', methods=['GET'])
def serve_xml(filename):
    """Serve .xml files from the configured directory."""
    if not filename.endswith('.xml'):
        return jsonify({'error': 'Only .xml files can be served'}), 400
    filepath = os.path.join(M3U_DIR, filename)
    if not os.path.isfile(filepath):
        return jsonify({'error': 'File not found'}), 404
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    return Response(content, content_type='application/xml')

@app.route('/generate', methods=['GET'])
def generate_m3u_from_xml():
    """Generate an m3u playlist dynamically from a youtubelinks.xml file in the data directory."""
    xml_filename = request.args.get('xml', 'youtubelinks.xml')
    xml_path = os.path.join(M3U_DIR, xml_filename)
    if not os.path.isfile(xml_path):
        return jsonify({'error': f'XML file not found: {xml_filename}'}), 404

    output_filename = os.path.splitext(xml_filename)[0] + '.m3u'
    output_path = os.path.join(M3U_DIR, output_filename)

    if not generate_m3u_from_xml_file(xml_path, output_path):
        return jsonify({'error': 'Failed to generate m3u from XML'}), 500

    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return Response(content, content_type='audio/x-mpegurl')

@app.route('/epg', methods=['GET'])
def generate_epg():
    """Generate an XMLTV EPG from a youtubelinks.xml file in the data directory."""
    xml_filename = request.args.get('xml', 'youtubelinks.xml')
    xml_path = os.path.join(M3U_DIR, xml_filename)
    if not os.path.isfile(xml_path):
        return jsonify({'error': f'XML file not found: {xml_filename}'}), 404

    output_filename = os.path.splitext(xml_filename)[0] + '_epg.xml'
    output_path = os.path.join(M3U_DIR, output_filename)

    if not generate_epg_from_xml_file(xml_path, output_path):
        return jsonify({'error': 'Failed to generate EPG'}), 500

    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return Response(content, content_type='application/xml')

@app.route('/epg/<path:filename>', methods=['GET'])
def serve_epg(filename):
    """Serve EPG .xml files from the configured directory."""
    if not filename.endswith('.xml'):
        return jsonify({'error': 'Only .xml files can be served'}), 400
    filepath = os.path.join(M3U_DIR, filename)
    if not os.path.isfile(filepath):
        return jsonify({'error': 'File not found'}), 404
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    return Response(content, content_type='application/xml')

@app.route('/stream', methods=['GET'])
def stream():
    url = unquote(request.args.get('url'))  # Decode URL-encoded characters
    if not url:
        return jsonify({'error': 'URL parameter is required'}), 400

    try:
        # Get stream info with more detailed output
        info_command = ['streamlink', '--json', '--loglevel', 'debug', url]
        info_process = subprocess.Popen(info_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        info_output, info_error = info_process.communicate()

        if info_process.returncode != 0:
            error_msg = info_error.decode('utf-8', errors='replace')
            logging.error(f'Streamlink error: {error_msg}')
            return jsonify({'error': 'Failed to retrieve stream info', 'details': error_msg}), 500

        # Parse the JSON output
        stream_info = json.loads(info_output.decode('utf-8', errors='replace'))

        # Check if streams are available
        if 'streams' not in stream_info or not stream_info['streams']:
            if 'youtube.com' in url.lower() or 'youtu.be' in url.lower():
                yt_command = ['yt-dlp', '--get-url', '--youtube-skip-dash-manifest', url]
                yt_process = subprocess.Popen(yt_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                yt_url, yt_error = yt_process.communicate()
                
                if yt_process.returncode != 0:
                    logging.error(f'yt-dlp error: {yt_error.decode("utf-8", errors="replace")}')
                    return jsonify({'error': 'No valid streams found'}), 404
                
                url = yt_url.decode('utf-8', errors='replace').strip()
                info_command = ['streamlink', '--json', url]
                info_process = subprocess.Popen(info_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                info_output, info_error = info_process.communicate()
                stream_info = json.loads(info_output.decode('utf-8', errors='replace'))

        best_quality = stream_info['streams'].get('best')
        if not best_quality:
            return jsonify({'error': 'No valid streams found'}), 404

        # Command to run Streamlink
        command = [
            'streamlink',
            url,
            'best',
            '--hls-live-restart',
            '--stdout'
        ]

        # Start the subprocess
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        client_ip = request.remote_addr

        def generate():
            try:
                logging.info(f"Starting stream for client {client_ip} from {url}")
                while True:
                    data = process.stdout.read(4096)
                    if not data:
                        break
                    yield data
            except GeneratorExit:
                logging.info(f"Client {client_ip} disconnected from stream {url}")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                finally:
                    process.stdout.close()
                    process.stderr.close()
            except Exception as e:
                logging.error(f'Error in generator for {client_ip}: {str(e)}')
                process.terminate()
                process.stdout.close()
                process.stderr.close()

        response = Response(generate(), content_type='video/mp2t')
        
        @response.call_on_close
        def cleanup():
            if process.poll() is None:
                logging.info(f"Cleaning up stream process for client {client_ip} from {url}")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                finally:
                    process.stdout.close()
                    process.stderr.close()

        return response

    except Exception as e:
        logging.error(f'Error occurred: {str(e)}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Generate youtubelive.m3u and EPG from youtubelinks.xml at startup if the XML exists
    xml_path = os.path.join(M3U_DIR, 'youtubelinks.xml')
    m3u_path = os.path.join(M3U_DIR, 'youtubelive.m3u')
    epg_path = os.path.join(M3U_DIR, 'youtubelinks_epg.xml')
    generate_m3u_from_xml_file(xml_path, m3u_path)
    generate_epg_from_xml_file(xml_path, epg_path)

    app.run(host='0.0.0.0', port=int(SERVER_PORT))