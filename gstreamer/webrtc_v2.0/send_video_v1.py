import json
import threading
import websocket
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstSdp', '1.0')
gi.require_version('GstWebRTC', '1.0')  # WebRTC関連を明示的に指定
from gi.repository import Gst, GstSdp, GstWebRTC

Gst.init(None)

# WebSocket接続
ws = websocket.WebSocket()
# ws.connect("ws://localhost:8080")
ws.connect("wss://webrtc.kskshome.xyz")
# ws.connect("ws://192.168.0.117:8080") # 本番ではwssでないと動かないらしい
ws.send(json.dumps({"role": "gstreamer"}))

# GStreamerパイプライン作成
pipeline = Gst.parse_launch(
    "autovideosrc ! videoconvert ! vp8enc deadline=1 ! rtpvp8pay ! "
    "application/x-rtp,media=video,encoding-name=VP8,payload=96 ! "
    "webrtcbin name=sendrecv"
)


# MAC用(ハードウェアエンコあり)
'''
pipeline = Gst.parse_launch(
    "autovideosrc ! video/x-raw,width=1280,height=720,framerate=30/1 ! "
    "videoconvert ! vtenc_h264 realtime=true allow-frame-reordering=false bitrate=1500 ! "
    "rtph264pay config-interval=1 pt=96 ! "
    "application/x-rtp,media=video,encoding-name=H264,payload=96 ! "
    "webrtcbin name=sendrecv latency=0"
)
'''


webrtcbin = pipeline.get_by_name("sendrecv")

# offer生成時のコールバック
def on_offer_created(promise, _):
    reply = promise.get_reply()
    offer = reply.get_value("offer")
    print("Created offer SDP:\n", offer.sdp.as_text()) 
    webrtcbin.emit("set-local-description", offer, None)

    text = offer.sdp.as_text()
    ws.send(json.dumps({
        "role": "gstreamer",
        "sdp": {
            "type": "offer",
            "sdp": text
        }
    }))

# ネゴシエーション開始時のコールバック
def on_negotiation_needed(element):
    promise = Gst.Promise.new_with_change_func(on_offer_created, None)
    element.emit("create-offer", None, promise)

webrtcbin.connect("on-negotiation-needed", on_negotiation_needed)

# ICE candidate 生成時のコールバック
def on_ice_candidate(element, mlineindex, candidate):
    ws.send(json.dumps({
        "role": "gstreamer",
        "candidate": {
            "candidate": candidate,
            "sdpMLineIndex": mlineindex
        }
    }))

webrtcbin.connect("on-ice-candidate", on_ice_candidate)

# WebSocket 受信処理
def listen_ws():
    while True:
        msg = ws.recv()
        data = json.loads(msg)

        if data.get("role") == "browser_ready":
            browser_ready.set()

        if "sdp" in data:
            if data["sdp"]["type"] == "answer":
                sdp = GstSdp.SDPMessage.new()
                res, sdpmsg = GstSdp.sdp_message_new()
                GstSdp.sdp_message_parse_buffer(data["sdp"]["sdp"].encode(), sdpmsg)
                answer = GstWebRTC.WebRTCSessionDescription.new(
                    GstWebRTC.WebRTCSDPType.ANSWER, sdpmsg
                )
                webrtcbin.emit("set-remote-description", answer, None)

        elif "candidate" in data:
            webrtcbin.emit("add-ice-candidate",
                           data["candidate"]["sdpMLineIndex"],
                           data["candidate"]["candidate"])

# WebSocket 受信スレッド起動
threading.Thread(target=listen_ws, daemon=True).start()

# パイプライン実行
pipeline.set_state(Gst.State.PLAYING)
print("Streaming started. Press Ctrl+C to stop.")

# メインループ維持
import time
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pipeline.set_state(Gst.State.NULL)
    print("Stopped.")
