import http.server as server
import urllib.request
import urllib.parse
import json
import re

ENV_FILE = "api_key.env"
YT_API_KEY = None
with open(ENV_FILE, "r") as f:
    line = f.readline().split("=")
    if line[0].strip() == "YT_API_KEY":
        YT_API_KEY = line[1].strip()

def get_videos_infos(video_ids):
    """
    Get the infos of the videos with the given ids.
    """
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id={','.join(video_ids)}&key={YT_API_KEY}"
    response = urllib.request.urlopen(url)
    data = json.loads(response.read().decode())
    return data["items"]


class HTTPRequestHandler(server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if not self.path.startswith("/?v="):
            self.send_response(200, "Path must start with '/?v='")
            return
        query = urllib.parse.parse_qs(self.path.split("?")[1])
        video_ids = query["v"][0].split(",")
        if len(video_ids) > 50:
            self.send_error(400, "Can only request 50 videos at once")
            return

        regexp = r"[a-z0-9_-]{11}"
        for v in video_ids:
            if not re.match(regexp, v, re.I):
                self.send_error(400, f'Not a valid youtube video id : "{v}"')
                return
        
        videos = get_videos_infos(video_ids)

        response_data = []
        for v in videos:
            response_data.append({
                "id": v["id"],
                'year' : int(v["snippet"]["publishedAt"].split("-")[0]),
                'views' : int(v["statistics"]["viewCount"]),
            })

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode())

        return

if __name__ == '__main__':
    if YT_API_KEY is None:
        print(f'Please set the YT_API_KEY environment variable in "{ENV_FILE}"')
        exit(1)

    PORT = 8282
    server_address = ("", PORT)

    handler = HTTPRequestHandler
    print("Server listening on port :", PORT)

    httpd = server.HTTPServer(server_address, handler)

    try:
        # httpd.serve_forever()
        server.test(HandlerClass=handler, port=PORT)
    except KeyboardInterrupt:
        pass

    # httpd.server_close()
    print("Server stopped.")
