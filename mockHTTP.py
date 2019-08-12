#!/usr/bin/python3

import http.server
import cgi
import socketserver
import hashlib
import json

PORT = 8081

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        info = {
            "method": "POST",
            "headers": { k: v for k, v in self.headers.items() },
        }

        # From https://snipt.net/raw/f8ef141069c3e7ac7e0134c6b58c25bf/?nice
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })

        postdata = {}
        for k in form.keys():
            if form[k].file:
                buf = form.getvalue(k)
                postdata[k] = {
                    "type": "file",
                    "name": form[k].filename,
                    "size": len(buf),
                    # json.dumps will not serialize a byte() object, so we
                    # return the shasum instead of the file body
                    "sha256": hashlib.sha256(buf).hexdigest(),
                }
            else:
                vals = form.getlist(k)
                if len(vals) == 1:
                    postdata[k] = {
                        "type": "field",
                        "val": vals[0],
                    }
                else:
                    postdata[k] = {
                        "type": "multifield",
                        "vals": vals,
                    }

        info["postdata"] = postdata

        resbody = json.dumps(info, indent=1)
        print(resbody)

        resbody = resbody.encode("utf-8")

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Content-Length", str(len(resbody)))
        self.end_headers()

        self.wfile.write(resbody)

class TCPServer(socketserver.TCPServer):
    # Allow to restart the mock server without needing to wait for the socket
    # to end TIME_WAIT: we only listen locally, and we may restart often in
    # some workflows
    allow_reuse_address = True

httpd = TCPServer(("", PORT), Handler)

print("serving at port", PORT)
httpd.serve_forever()
