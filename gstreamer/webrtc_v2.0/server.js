const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const os = require('os'); 

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

app.use(express.static('public'));

let gst = null;
let browser = null;

wss.on('connection', socket => {
  console.log('New WebSocket connection');
  
  socket.on('message', message => {
    const msg = JSON.parse(message);

    if (msg.role === 'gstreamer') {
      console.log('GStreamer connected');
      gst = socket;
    } else if (msg.role === 'browser') {
      console.log('Browser connected');
      browser = socket;
    }

    // browser_ready も中継しないと GStreamer 側の create-offer が呼ばれない
    if (msg.role === 'browser_ready' && gst) {
      console.log('Browser is ready, notifying GStreamer');
      if (gst.readyState === WebSocket.OPEN) {
        gst.send(JSON.stringify(msg));
      }
    }

    // SDP / candidate 中継
    if (gst && browser) {
      const peer = (socket === gst) ? browser : gst;
      if (peer.readyState === WebSocket.OPEN) {
        peer.send(JSON.stringify(msg));
      } else {
        console.warn('Target socket not open');
      }
    }
  });

  socket.on('close', () => {
    if (socket === gst) {
      console.log('GStreamer disconnected');
      gst = null;
    }
    if (socket === browser) {
      console.log('Browser disconnected');
      browser = null;
    }
  });
});

server.listen(8080, () => {
  const interfaces = os.networkInterfaces();
  const addresses = [];
  for (const iface of Object.values(interfaces)) {
    for (const config of iface) {
      if (config.family === 'IPv4' && !config.internal) {
        addresses.push(config.address);
      }
    }
  }
  console.log('Signaling server running at:');
  addresses.forEach(addr => {
    console.log(`  http://${addr}:8080`);
  });
});
