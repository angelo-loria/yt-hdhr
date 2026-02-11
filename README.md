# youtube-to-m3u

A containerized Flask server that proxies YouTube live streams, making them playable in any IPTV player via M3U playlists.

## How It Works

The server uses [Streamlink](https://streamlink.github.io/) and [yt-dlp](https://github.com/yt-dlp/yt-dlp) to resolve YouTube live stream URLs on the fly. Define your channels in a simple XML file, and the container automatically generates an M3U playlist and XMLTV EPG at startup.

## Important Note

The m3u/extracted m3u8 links will only work on machines that have the same public IP address (on the same local network) as the machine running the container. To play on a client with a different public IP, load the m3u into an m3u proxy such as [Threadfin](https://github.com/Threadfin/Threadfin) to restream.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/) (included with Docker Desktop)

## Quick Start

1. Update the volume in `docker-compose.yml` to mount your local `data/` directory:

   ```yaml
   volumes:
     - ./data:/data
   ```

   Place your `youtubelinks.xml` file in the `data/` directory to define your channels. At container startup, the server will automatically generate `youtubelive.m3u` and `youtubelinks_epg.xml` from it.

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

6. Access your EPG at:

```
http://<HOST_IP>:6095/epg/youtubelinks_epg.xml
```

## Build and Run Manually

```bash
docker build -t youtube-live .
docker run -p 6095:6095 -v ./data:/data -e HOST_IP=192.168.1.123 -e SERVER_PORT=6095 youtube-live
```

## Docker Compose Configuration

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

## Environment Variables

| Variable      | Description                                  | Default         |
| ------------- | -------------------------------------------- | --------------- |
| `HOST_IP`     | IP address used in generated m3u stream URLs | `192.168.1.123` |
| `SERVER_PORT` | Port the Flask server listens on             | `6095`          |
| `M3U_DIR`     | Directory for m3u/xml files inside container | `/data`         |

## Channel Configuration via XML

Define your channels in `youtubelinks.xml` and place it in the `data/` directory. The server will automatically generate `youtubelive.m3u` and an XMLTV EPG file (`youtubelinks_epg.xml`) at startup. Channel numbers are automatically assigned based on order, or you can set them explicitly with `<channel-number>`.

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

### XML Field Reference

| Field            | Description                                                         | Required |
| ---------------- | ------------------------------------------------------------------- | -------- |
| `channel-name`   | Display name of the channel                                         | Yes      |
| `tvg-id`         | EPG tag matching your EPG source's tvg-id                           | No       |
| `tvg-name`       | Channel name used in the m3u tvg-name attribute                     | No       |
| `tvg-logo`       | Direct URL to the channel logo image                                | No       |
| `group-title`    | Group the channel appears in (e.g., News, Sports)                   | No       |
| `channel-number` | Channel number (auto-assigned if omitted)                           | No       |
| `youtube-url`    | YouTube live stream URL — `@channelname/live` or `/watch?v=` format | Yes      |

You can also regenerate the m3u and EPG on-demand (e.g., after editing the XML) by visiting:

```
http://<HOST_IP>:6095/generate
http://<HOST_IP>:6095/epg
```

## Endpoints

| Endpoint                    | Description                                                       |
| --------------------------- | ----------------------------------------------------------------- |
| `/stream?url=<youtube-url>` | Proxies a YouTube live stream via Streamlink                      |
| `/m3u/<filename>`           | Serves `.m3u` files from the data directory                       |
| `/xml/<filename>`           | Serves `.xml` files from the data directory                       |
| `/epg/<filename>`           | Serves EPG `.xml` files from the data directory                   |
| `/generate`                 | Generates `youtubelive.m3u` from `youtubelinks.xml` and serves it |
| `/generate?xml=<filename>`  | Generates an m3u from a custom XML file                           |
| `/epg`                      | Generates EPG from `youtubelinks.xml` and serves it               |
| `/epg?xml=<filename>`       | Generates EPG from a custom XML file                              |
