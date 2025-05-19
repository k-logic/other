const express = require('express');
const http = require('http');
const WebSocket = require('ws');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

let gst = null;
let browser = null;

wss.on('connection', socket => {
  socket.on('message', message => {
    const msg = JSON.parse(message);

    if (msg.role === 'gstreamer') {
      gst = socket;
    } else if (msg.role === 'browser') {
      browser = socket;
    }

    // 中継
    if (gst && browser) {
      const peer = (socket === gst) ? browser : gst;
      peer.send(JSON.stringify(msg));
    }
  });

  socket.on('close', () => {
    if (socket === gst) gst = null;
    if (socket === browser) browser = null;
  });
});

app.use(express.static('public'));
server.listen(8080, () => {
  console.log('Signaling server running on http://localhost:8080');
});
