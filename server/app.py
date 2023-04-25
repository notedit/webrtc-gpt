

import uuid
import logging

from sanic import Sanic
from sanic.log import logger
from sanic.response import text, json
from sanic_cors import CORS, cross_origin

from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder, MediaRelay

app = Sanic("webrtc-gpt")

CORS(app)

pcs = set()


@app.get("/test")
async def hello_world(request):
    return text("Hello, world.")


@app.post('/offer')
async def offer(request):
    params = request.json
    offer = RTCSessionDescription(sdp=params["sdp"], type='offer')

    pc = RTCPeerConnection()
    pc_id = uuid.uuid4().hex
    pc.id = pc_id
    pcs.add(pc)

    def log_info(msg, *args):
        logger.info(pc_id + " " + msg, *args)

    # todo add audio track

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            if isinstance(message, str) and message.startswith("ping"):
                channel.send("pong" + message[4:])

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        log_info("Connection state is %s", pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    @pc.on("track")
    def on_track(track):
        log_info("Track %s received", track.kind)

        if track.kind == "audio":
            pass
        elif track.kind == "video":
            pass

        @track.on("ended")
        async def on_ended():
            log_info("Track %s ended", track.kind)

    # handle offer
    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return json({"sdp": pc.localDescription.sdp})
