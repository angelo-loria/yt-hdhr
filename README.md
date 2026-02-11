# youtube-to-m3u

Play YouTube live streams in any player

## Important Note

The m3u/extracted m3u8 links will only work on machines that have the same public IP address (on the same local network) as the machine that extracted them. To play on a client that has a different public IP (on a different network) use a non flask version and load the m3u into a m3u proxy such as threadfin to restream

## Choose script option

youtube-live.py - Uses a flask server to automatically pull the actuall stream link. Server needs to be running all the time for m3u to work. Best for always working stream<br>
<br>
youtube-non-server.py - Pulls stream link into m3u but script will have to manually run (or cron job) every few hours as the stream links will expire <br>
<br>
youtube_non_stream_link.py - Same as youtube-non-server.py but doesn't require streamlink - only use if you are unable to install streamlink as if anything changes youtube side the script will need updating instead of just updating streamlink

## Docker (Recommended for youtube-live.py)

The easiest way to run `youtube-live.py` is with Docker.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/) (included with Docker Desktop)

### Quick Start

1. Place your `youtubelinks.xml` file in the `data/` directory to define your channels. At container startup, the server will automatically generate `youtubelive.m3u` from it.

2. Configure your environment variables in `docker-compose.yml`:
   - `HOST_IP` — the IP address of the machine running the container
   - `SERVER_PORT` — the port the server listens on (default `6095`)
   - `M3U_DIR` — the directory for data files inside the container (default `/data`)

3. Start the container:

```bash
docker compose up -d
```

4. The server will be available at `http://<HOST_IP>:6095`

5. Access your m3u playlist at:

```
http://<HOST_IP>:6095/m3u/youtubelive.m3u
```

### Build and Run Manually

```bash
docker build -t youtube-live .
docker run -p 6095:6095 -v ./data:/data -e HOST_IP=192.168.1.123 -e SERVER_PORT=6095 youtube-live
```

### Docker Compose Configuration

The `docker-compose.yml` mounts the local `./data` directory into the container at `/data`. Environment variables control the host IP, port, and data directory. At startup, if `youtubelinks.xml` is present in the data directory, the server automatically generates `youtubelive.m3u` and `youtubelinks_epg.xml` from it.

```yaml
services:
  youtube-live:
    build: .
    container_name: youtube-live
    ports:
      - "6095:6095"
    volumes:
      - ./data:/data
    environment:
      - M3U_DIR=/data
      - HOST_IP=192.168.1.123
      - SERVER_PORT=6095
    restart: unless-stopped
```

### Environment Variables

| Variable      | Description                                  | Default         |
| ------------- | -------------------------------------------- | --------------- |
| `HOST_IP`     | IP address used in generated m3u stream URLs | `192.168.1.123` |
| `SERVER_PORT` | Port the Flask server listens on             | `6095`          |
| `M3U_DIR`     | Directory for m3u/xml files inside container | `/data`         |

### Channel Configuration via XML

Instead of manually editing `.m3u` files, you can define your channels in `youtubelinks.xml` and place it in the `data/` directory. The server will automatically generate `youtubelive.m3u` and an XMLTV EPG file (`youtubelinks_epg.xml`) at startup.

```xml
<channels>
    <channel>
        <channel-name>ABC News</channel-name>
        <tvg-id>ABCNEWS.us</tvg-id>
        <tvg-name>ABC News</tvg-name>
        <tvg-logo>https://example.com/logo.png</tvg-logo>
        <group-title>News</group-title>
        <channel-number>1</channel-number>
        <youtube-url>https://www.youtube.com/@abcnews/live</youtube-url>
    </channel>
</channels>
```

You can also regenerate the m3u on-demand (e.g., after editing the XML) by visiting:

```
http://<HOST_IP>:6095/generate
```

### Endpoints

| Endpoint                    | Description                                                       |
| --------------------------- | ----------------------------------------------------------------- |
| `/stream?url=<youtube-url>` | Proxies a YouTube live stream via Streamlink                      |
| `/m3u/<filename>`           | Serves `.m3u` files from the data directory                       |
| `/xml/<filename>`           | Serves `.xml` files from the data directory                       |
| `/generate`                 | Generates `youtubelive.m3u` from `youtubelinks.xml` and serves it |
| `/generate?xml=<filename>`  | Generates an m3u from a custom XML file                           |

## Requirements (Non-Docker)

### All Versions

python - must be 3.10 or higher (3.8 or lower is not supported by streamlink) <br>
requests (can be installed by typing `pip install requests` at cmd/terminal window) <br>

### All Versions except youtube_non_stream_link.py

install [streamlink](https://streamlink.github.io/install.html) and make it available at path

### youtube-live.py only <br>

flask (can be installed by typing `pip install flask` at cmd/terminal window) <br>
yt-dlp (can be installed by typing `pip install yt-dlp` at cmd/terminal window) <br>
youtubelive.m3u

### youtube-non-server.py and youtube_non_stream_link.py<br>

youtubelinks.xml

## Verify streamlink install

To test streamlink install type in a new cmd/terminal window

```
streamlink --version
```

The output should be
streamlink "version number" eg 8.1.2 <br>
If it says unknown command/'streamlink' is not recognized as an internal or external command,
operable program or batch file. <br>
Then you need to make sure you have installed streamlink to path/environmental variables

## How To Use youtube-live.py

Open youtubelive.m3u <br>
Change the ip address in the streamlink to the ip address of the machine running the script <br>
You can also change the port but if you do this you must change the port to match at the bottom of youtube-live.py <br>
<br>
To add other live streams just add into m3u in the following format

```
#EXTINF:-1 tvg-name="Channel Name" tvg-id="24.7.Dummy.us" tvg-logo="https://upload.wikimedia.org/wikipedia/commons/thumb/5/54/YouTube_dark_logo_2017.svg/2560px-YouTube_dark_logo_2017.svg.png" group-title="YouTube",Channel Name
http://192.168.1.123:6095/stream?url=https://www.youtube.com/@ChannelName/live
```

Or if the channel has multiple live streams you can use the /watch? link however these links will change if the channel stops and restarts broadcast <br>
<br>
You can change tvg-name tvg-logo group-title and channel name and if you want to link to an epg change tvg-id to match your epgs tvg-id for that channel <br>
(The two sample streams link to the epg from epgshare01.online UK and USA epgs) <br>
<br>
Run the python script <br>
python youtube-live.py or python3 youtube-live.py if you have the old python2 installed <br>
<br>
Script must be running for the m3u to work

## How To Use youtube-non-server.py or youtube_non_stream_link.py

Open youtubelinks.xml in a code text editor eg notepad++ <br>
Add in your channel details for your youtube stream in the following format

```
<channel>
        <channel-name>ABC News</channel-name>
        <tvg-id>ABCNEWS.us</tvg-id>
        <tvg-name>ABC News</tvg-name>
        <tvg-logo>https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/abc-news-light-us.png?raw=true</tvg-logo>
        <group-title>News</group-title>
        <youtube-url>https://www.youtube.com/@abcnews/live</youtube-url>
    </channel>
```

channel-name = name of channel <br>
tvg-id = epg tag which matches tvg-id in your epg (you can enter anything here if you don't have an epg or leave blank) <br>
tvg-name = name of channel <br>
tvg-logo = direct link to channel logo png <br>
group-title = group you want channel to appear in <br>
youtube-url = url to youtube live stream - can be @channelname/live or /watch? <br>
<br>
Run the python script <br>
python youtube-non-server.py or python3 youtube-non-server.py if you have the old python2 installed <br>
<br>
As the stream links will expire you will need to setup a cron job/scheduled task or manually run the script every few hours <br>
To have the stream urls automatically be pulled use the flask version <br>
<br>
