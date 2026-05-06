document.addEventListener("DOMContentLoaded", () => {
  const startButton = document.getElementById("start-voice-session");
  const stopButton = document.getElementById("stop-voice-session");
  const statusEl = document.getElementById("voice-status");
  const logEl = document.getElementById("realtime-log");
  const audioEl = document.getElementById("realtime-audio");

  let peerConnection = null;
  let dataChannel = null;
  let localStream = null;
  let handledCallIds = new Set();

  const log = (message, payload) => {
    const timestamp = new Date().toLocaleTimeString();
    const lines = [`[${timestamp}] ${message}`];
    if (payload !== undefined) {
      if (typeof payload === "string") {
        lines.push(payload);
      } else {
        lines.push(JSON.stringify(payload, null, 2));
      }
    }
    logEl.textContent = `${lines.join("\n")}\n\n${logEl.textContent}`.trim();
  };

  const setStatus = (message) => {
    statusEl.textContent = message;
  };

  const setButtons = (connected) => {
    startButton.disabled = connected;
    stopButton.disabled = !connected;
  };

  const safeJsonParse = (value) => {
    try {
      return JSON.parse(value);
    } catch (error) {
      return null;
    }
  };

  const sendRealtimeEvent = (event) => {
    if (!dataChannel || dataChannel.readyState !== "open") {
      throw new Error("Realtime data channel is not open.");
    }
    dataChannel.send(JSON.stringify(event));
  };

  const handleToolCall = async (event) => {
    const callId = event.call_id || (event.item && event.item.call_id);
    const toolName = event.name || (event.item && event.item.name);
    const rawArguments = event.arguments || (event.item && event.item.arguments) || "{}";

    if (!callId || !toolName) {
      log("Received malformed tool call event.", event);
      return;
    }
    if (handledCallIds.has(callId)) {
      return;
    }
    handledCallIds.add(callId);

    const parsedArguments = typeof rawArguments === "string" ? safeJsonParse(rawArguments) : rawArguments;
    if (parsedArguments === null) {
      log(`Failed to parse tool arguments for ${toolName}.`, rawArguments);
      return;
    }

    log(`Calling backend tool: ${toolName}`, parsedArguments);

    const response = await fetch("/realtime/tool", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        call_id: callId,
        name: toolName,
        arguments: parsedArguments,
      }),
    });

    const payload = await response.json();
    if (!response.ok) {
      log(`Backend tool failed: ${toolName}`, payload);
      throw new Error(payload.error || `Tool call failed for ${toolName}.`);
    }

    log(`Backend tool result: ${toolName}`, payload.result);

    sendRealtimeEvent({
      type: "conversation.item.create",
      item: {
        type: "function_call_output",
        call_id: callId,
        output: JSON.stringify(payload.result),
      },
    });
    sendRealtimeEvent({
      type: "response.create",
    });
  };

  const stopSession = () => {
    handledCallIds = new Set();

    if (dataChannel) {
      try {
        dataChannel.close();
      } catch (error) {
        // no-op
      }
      dataChannel = null;
    }

    if (peerConnection) {
      try {
        peerConnection.close();
      } catch (error) {
        // no-op
      }
      peerConnection = null;
    }

    if (localStream) {
      localStream.getTracks().forEach((track) => track.stop());
      localStream = null;
    }

    if (audioEl) {
      audioEl.srcObject = null;
    }

    setStatus("Disconnected");
    setButtons(false);
  };

  const attachDataChannel = (channel) => {
    dataChannel = channel;

    dataChannel.addEventListener("open", () => {
      setStatus("Connected");
      log("Realtime data channel opened.");
    });

    dataChannel.addEventListener("close", () => {
      log("Realtime data channel closed.");
    });

    dataChannel.addEventListener("message", async (messageEvent) => {
      let event;
      try {
        event = JSON.parse(messageEvent.data);
      } catch (error) {
        log("Received non-JSON Realtime event.");
        return;
      }

      const eventType = event.type || "unknown";

      if (eventType === "session.created") {
        log("Realtime session created.", {
          session_id: event.session && event.session.id,
          model: event.session && event.session.model,
        });
        return;
      }

      if (eventType === "response.function_call_arguments.done") {
        try {
          await handleToolCall(event);
        } catch (error) {
          log("Tool dispatch error.", error.message);
        }
        return;
      }

      if (
        eventType === "conversation.item.done" &&
        event.item &&
        event.item.type === "function_call"
      ) {
        try {
          await handleToolCall(event);
        } catch (error) {
          log("Tool dispatch error.", error.message);
        }
        return;
      }

      if (eventType === "response.text.done") {
        log("Assistant text response.", event.text);
        return;
      }

      if (eventType === "conversation.item.input_audio_transcription.completed") {
        log("User transcript.", event.transcript);
        return;
      }

      if (eventType === "error") {
        log("Realtime error.", event);
        return;
      }

      if (
        [
          "response.created",
          "response.done",
          "conversation.item.created",
          "output_audio_buffer.started",
          "output_audio_buffer.stopped",
        ].includes(eventType)
      ) {
        log(`Realtime event: ${eventType}`);
      }
    });
  };

  const startSession = async () => {
    setStatus("Requesting microphone access...");
    setButtons(true);
    log("Starting Realtime voice session.");

    try {
      const tokenResponse = await fetch("/realtime/session", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });
      const tokenPayload = await tokenResponse.json();
      if (!tokenResponse.ok) {
        throw new Error(tokenPayload.error || "Failed to create a Realtime session.");
      }

      const ephemeralKey = tokenPayload.client_secret;
      if (!ephemeralKey) {
        throw new Error("Realtime client secret was missing.");
      }

      localStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      peerConnection = new RTCPeerConnection();

      peerConnection.ontrack = (event) => {
        audioEl.srcObject = event.streams[0];
      };

      peerConnection.onconnectionstatechange = () => {
        log(`Peer connection state: ${peerConnection.connectionState}`);
        if (["failed", "disconnected", "closed"].includes(peerConnection.connectionState)) {
          stopSession();
        }
      };

      localStream.getTracks().forEach((track) => {
        peerConnection.addTrack(track, localStream);
      });

      attachDataChannel(peerConnection.createDataChannel("oai-events"));

      const offer = await peerConnection.createOffer();
      await peerConnection.setLocalDescription(offer);

      setStatus("Connecting to OpenAI Realtime...");

      const sdpResponse = await fetch("https://api.openai.com/v1/realtime/calls", {
        method: "POST",
        body: offer.sdp,
        headers: {
          "Authorization": `Bearer ${ephemeralKey}`,
          "Content-Type": "application/sdp",
        },
      });

      if (!sdpResponse.ok) {
        const errorText = await sdpResponse.text();
        throw new Error(`OpenAI Realtime connection failed: ${errorText}`);
      }

      const answerSdp = await sdpResponse.text();
      await peerConnection.setRemoteDescription({
        type: "answer",
        sdp: answerSdp,
      });

      setStatus("Waiting for speech...");
      log("Realtime WebRTC session established.", tokenPayload.session || {});
    } catch (error) {
      log("Voice session failed.", error.message);
      stopSession();
    }
  };

  startButton.addEventListener("click", () => {
    startSession();
  });

  stopButton.addEventListener("click", () => {
    log("Ending Realtime voice session.");
    stopSession();
  });

  setButtons(false);
});
