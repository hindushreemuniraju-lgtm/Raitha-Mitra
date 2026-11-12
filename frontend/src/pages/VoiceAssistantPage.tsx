import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Room, RoomEvent } from "livekit-client";
import {
  Mic,
  MicOff,
  Square,
  Send,
  Volume2,
  Camera,
  Radio,
} from "lucide-react";
import {
  ErrorState,
  IntegrationStatusBadge,
} from "@/components/common/StateFeedback";
import { VoiceWaveform } from "@/components/voice/VoiceWaveform";
import { useAuth } from "@/context/AuthContext";
import { SUPPORTED_LANGUAGES, useLanguage } from "@/context/LanguageContext";
import { api } from "@/services/api";
import type { LanguageCode, VoiceMessage, VoiceTokenResponse } from "@/types";

export const VoiceAssistantPage: React.FC = () => {
  const { farmer } = useAuth();
  const { language, setLanguage } = useLanguage();

  const [selectedLang, setSelectedLang] = useState<LanguageCode>(
    (farmer?.preferred_language as LanguageCode) || language || "kn-IN"
  );
  const [sessionId, setSessionId] = useState<number | undefined>(undefined);
  const [messages, setMessages] = useState<VoiceMessage[]>([]);
  const [textInput, setTextInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Voice & LiveKit state
  const [tokenInfo, setTokenInfo] = useState<VoiceTokenResponse | null>(null);
  const [lkConnected, setLkConnected] = useState(false);
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [muted, setMuted] = useState(false);
  const [missingPhotoPrompt, setMissingPhotoPrompt] = useState<string | null>(null);

  const roomRef = useRef<Room | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Stop any playing assistant audio immediately (barge-in interruption)
  const stopAssistantAudioImmediately = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    setSpeaking(false);
  };

  useEffect(() => {
    api
      .createLiveKitToken({ language_code: selectedLang })
      .then((res) => setTokenInfo(res))
      .catch(() => {});

    return () => {
      stopAssistantAudioImmediately();
      roomRef.current?.disconnect();
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleLanguageChange = (code: LanguageCode) => {
    setSelectedLang(code);
    setLanguage(code);
    stopAssistantAudioImmediately();
  };

  const handlePlayFarmBriefing = async () => {
    stopAssistantAudioImmediately();
    setError(null);
    setLoading(true);
    try {
      const prompt =
        selectedLang === "kn-IN"
          ? "ನಮಸ್ಕಾರ! ನಾಳೆ ಮಳೆ ಸಾಧ್ಯತೆ, ಪ್ರವಾಹ ಎಚ್ಚರಿಕೆ ಮತ್ತು ನನ್ನ ಬೆಳೆ ಕೊಯ್ಲು ಮುನ್ನೆಚ್ಚರಿಕೆಗಳ ಬಗ್ಗೆ ತಿಳಿಸಿ."
          : "Hello! Give me today's weather, flood status, and crop harvest protection briefing for my farm.";
      const res = await api.sendVoiceTextTurn({
        text: prompt,
        language_code: selectedLang,
        session_id: sessionId,
      });
      setSessionId(res.session_id);
      setMessages(res.messages);
      if (res.audio_base64) {
        playReplyAudio(res.audio_base64, res.audio_mime);
      } else if (!muted && typeof window !== "undefined" && "speechSynthesis" in window) {
        const prefix = selectedLang === "kn-IN" ? "ನಮಸ್ಕಾರ ರೈತರೆ! " : "";
        const utter = new SpeechSynthesisUtterance(`${prefix}${res.reply_text}`);
        utter.lang = selectedLang || "kn-IN";
        setSpeaking(true);
        utter.onend = () => setSpeaking(false);
        utter.onerror = () => setSpeaking(false);
        window.speechSynthesis.speak(utter);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not generate farm voice briefing");
    } finally {
      setLoading(false);
    }
  };

  const playReplyAudio = (audioBase64?: string | null, audioMime?: string | null) => {
    stopAssistantAudioImmediately();
    if (!audioBase64 || muted) return;
    const audio = new Audio(`data:${audioMime || "audio/wav"};base64,${audioBase64}`);
    audioRef.current = audio;
    setSpeaking(true);
    audio.onended = () => setSpeaking(false);
    audio.onerror = () => setSpeaking(false);
    void audio.play().catch(() => setSpeaking(false));
  };

  const connectLiveKitRoom = async () => {
    setError(null);
    try {
      const tok = await api.createLiveKitToken({
        language_code: selectedLang,
        session_id: sessionId,
      });
      setTokenInfo(tok);
      if (!tok.livekit_configured || !tok.livekit_url || !tok.token) {
        setError(tok.note);
        return;
      }
      const room = new Room();
      room.on(RoomEvent.Disconnected, () => setLkConnected(false));
      await room.connect(tok.livekit_url, tok.token);
      await room.localParticipant.setMicrophoneEnabled(true);
      roomRef.current = room;
      setLkConnected(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not connect to LiveKit room.");
    }
  };

  const startRecording = async () => {
    // Interruption: farmer tapping mic immediately silences assistant speech
    const wasSpeaking = speaking;
    stopAssistantAudioImmediately();
    setError(null);

    if (lkConnected && roomRef.current) {
      await roomRef.current.localParticipant.setMicrophoneEnabled(!muted);
      setListening(true);
      return;
    }

    if (!navigator.mediaDevices?.getUserMedia) {
      setError("Microphone recording is not supported in this browser. Type your question below.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (ev) => {
        if (ev.data.size > 0) chunksRef.current.push(ev.data);
      };
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        if (blob.size === 0) return;
        setLoading(true);
        try {
          const res = await api.sendVoiceAudioTurn(blob, selectedLang, sessionId);
          setSessionId(res.session_id);
          setMessages(res.messages);
          setMissingPhotoPrompt(res.missing_data_prompt || null);
          playReplyAudio(res.audio_base64, res.audio_mime);
        } catch (err) {
          setError(err instanceof Error ? err.message : "Audio recognition failed");
        } finally {
          setLoading(false);
        }
      };
      recorderRef.current = recorder;
      recorder.start();
      setListening(true);
      if (wasSpeaking) {
        // Immediate barge-in acknowledged
      }
    } catch {
      setError("Microphone permission denied. Please allow mic access or type below.");
    }
  };

  const stopRecordingOrInterrupt = () => {
    stopAssistantAudioImmediately();
    if (recorderRef.current && recorderRef.current.state === "recording") {
      recorderRef.current.stop();
    }
    if (roomRef.current && lkConnected) {
      void roomRef.current.localParticipant.setMicrophoneEnabled(false);
    }
    setListening(false);
  };

  const handleSendText = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = textInput.trim();
    if (!trimmed) return;
    const wasSpeaking = speaking;
    stopAssistantAudioImmediately();
    setTextInput("");
    setLoading(true);
    setError(null);
    try {
      const res = await api.sendVoiceTextTurn({
        text: trimmed,
        language_code: selectedLang,
        session_id: sessionId,
        interrupted_previous: wasSpeaking,
      });
      setSessionId(res.session_id);
      setMessages(res.messages);
      setMissingPhotoPrompt(res.missing_data_prompt || null);
      playReplyAudio(res.audio_base64, res.audio_mime);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get voice assistant reply.");
    } finally {
      setLoading(false);
    }
  };

  const waveformMode = listening ? "listening" : speaking ? "speaking" : "idle";

  return (
    <div className="space-y-5">
      {/* Header & Connection Badges */}
      <div className="rm-card p-5 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-deep">Raitha Mitra Voice Assistant</h1>
          <p className="text-xs text-muted mt-1">
            Grounded in your farm profile ({farmer?.district || farmer?.state} •{" "}
            {farmer?.main_crops?.join(", ") || "Crops not set"}). Replies stay in your selected language.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1.5 text-xs">
            <span>LiveKit:</span>
            <IntegrationStatusBadge
              status={lkConnected ? "configured" : tokenInfo?.livekit_configured ? "ready" : "not_configured"}
              label={lkConnected ? "Connected" : tokenInfo?.livekit_configured ? "Ready" : "Not Configured"}
            />
          </div>
          <div className="flex items-center gap-1.5 text-xs">
            <span>Sarvam AI:</span>
            <IntegrationStatusBadge
              status={tokenInfo?.sarvam_configured ? "configured" : "not_configured"}
            />
          </div>
          <select
            aria-label="Voice Assistant Language"
            value={selectedLang}
            onChange={(e) => handleLanguageChange(e.target.value as LanguageCode)}
            className="rm-input w-44 py-1.5 text-xs font-semibold"
          >
            {SUPPORTED_LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.nativeName} ({lang.name})
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && <ErrorState message={error} />}

      {missingPhotoPrompt && (
        <div className="rounded-2xl border border-warning/40 bg-warning/10 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-[#6B4600]">
          <span>{missingPhotoPrompt}</span>
          <Link to="/pest-detection" className="rm-btn-secondary py-1.5 px-3 text-xs shrink-0">
            <Camera className="h-3.5 w-3.5" />
            Upload Crop Photo
          </Link>
        </div>
      )}

      {/* Voice Controls & Waveform */}
      <div className="rm-card p-6 flex flex-col items-center gap-4 text-center">
        <VoiceWaveform active={listening || speaking} mode={waveformMode} />

        <p className="text-xs font-semibold text-deep">
          {listening
            ? "Listening... Tap Stop when finished speaking"
            : speaking
            ? "Raitha Mitra is speaking... Tap Mic or Interrupt to stop immediately"
            : loading
            ? "Processing with farmer context..."
            : "Tap the microphone to speak or type below"}
        </p>

        <div className="flex flex-wrap items-center justify-center gap-3">
          {!listening ? (
            <button
              type="button"
              onClick={() => void startRecording()}
              className="inline-flex items-center gap-2 rounded-full bg-forest px-6 py-3.5 text-sm font-bold text-white shadow-soft hover:bg-deep transition-colors"
            >
              <Mic className="h-5 w-5" />
              Start Speaking
            </button>
          ) : (
            <button
              type="button"
              onClick={stopRecordingOrInterrupt}
              className="inline-flex items-center gap-2 rounded-full bg-danger px-6 py-3.5 text-sm font-bold text-white shadow-soft"
            >
              <Square className="h-4 w-4" />
              Stop & Send
            </button>
          )}

          {speaking && (
            <button
              type="button"
              onClick={stopAssistantAudioImmediately}
              className="rm-btn-secondary border-danger/40 text-danger"
            >
              <Square className="h-4 w-4" />
              Interrupt Reply
            </button>
          )}

          <button
            type="button"
            onClick={() => {
              const next = !muted;
              setMuted(next);
              if (next) stopAssistantAudioImmediately();
            }}
            className="rm-btn-secondary"
            aria-label="Toggle voice audio output"
          >
            {muted ? <MicOff className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
            {muted ? "Muted" : "Audio On"}
          </button>

          {!lkConnected && tokenInfo?.livekit_configured && (
            <button
              type="button"
              onClick={() => void connectLiveKitRoom()}
              className="rm-btn-secondary"
            >
              <Radio className="h-4 w-4 text-forest" />
              Connect LiveKit Room
            </button>
          )}

          <button
            type="button"
            onClick={() => void handlePlayFarmBriefing()}
            disabled={loading}
            className="rm-btn-secondary"
          >
            <Volume2 className="h-4 w-4 text-forest" />
            {selectedLang === "kn-IN" ? "ಕನ್ನಡ ಹವಾಮಾನ & ಕೊಯ್ಲು ವರದಿ ಕೇಳಿ" : "Speak Farm Weather & Harvest Alert"}
          </button>
        </div>
      </div>

      {/* Transcript & Reply Conversation */}
      <div className="rm-card p-5 space-y-4">
        <h2 className="text-sm font-bold text-deep">Conversation Transcript</h2>
        <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
          {messages.length === 0 ? (
            <p className="text-xs text-muted py-6 text-center">
              Ask about irrigation, fertilizer schedule, weather alerts, or mandi prices in your selected language.
            </p>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === "farmer" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                    msg.role === "farmer"
                      ? "bg-forest text-white"
                      : "bg-mint text-ink border border-[#176B35]/15"
                  }`}
                >
                  <p className="text-[10px] uppercase tracking-wider opacity-75 mb-1">
                    {msg.role === "farmer" ? "You (Recognized)" : "Raitha Mitra"} • {msg.language_code}
                    {msg.interrupted ? " • Interrupted" : ""}
                  </p>
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                  {msg.role === "assistant" && typeof window !== "undefined" && "speechSynthesis" in window && (
                    <button
                      type="button"
                      onClick={() => {
                        stopAssistantAudioImmediately();
                        const utter = new SpeechSynthesisUtterance(msg.content);
                        utter.lang = msg.language_code || selectedLang;
                        setSpeaking(true);
                        utter.onend = () => setSpeaking(false);
                        window.speechSynthesis.speak(utter);
                      }}
                      className="mt-2 inline-flex items-center gap-1 text-[11px] font-semibold text-forest hover:underline"
                    >
                      <Volume2 className="h-3 w-3" /> Speak in {msg.language_code}
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        <div className="flex flex-wrap gap-2 pt-1">
          {[
            { label: "ನಾಳೆ ಮಳೆಯಾಗುತ್ತದೆಯೇ? / Will it rain tomorrow?", text: selectedLang === "kn-IN" ? "ನಾಳೆ ಮಳೆಯಾಗುತ್ತದೆಯೇ?" : "Will it rain tomorrow?" },
            { label: "ಪ್ರವಾಹ ಎಚ್ಚರಿಕೆ ಇದೆಯೇ? / Any flood warning?", text: selectedLang === "kn-IN" ? "ನನ್ನ ಪ್ರದೇಶದಲ್ಲಿ ಪ್ರವಾಹ ಎಚ್ಚರಿಕೆ ಇದೆಯೇ?" : "Is there a flood warning in my area?" },
            { label: "ಇಂದು ಕೊಯ್ಲು ಮಾಡಬಹುದೇ? / Harvest today?", text: selectedLang === "kn-IN" ? "ನಾನು ಇಂದು ನನ್ನ ಬೆಳೆ ಕೊಯ್ಲು ಮಾಡಬೇಕೇ?" : "Should I harvest my crop today?" },
            { label: "ಎಷ್ಟು ದಿನ ಬಾಕಿ ಇದೆ? / Days remaining?", text: selectedLang === "kn-IN" ? "ಕೊಯ್ಲಿಗೆ ಎಷ್ಟು ದಿನ ಬಾಕಿ ಇದೆ?" : "How many days are remaining before harvest?" },
            { label: "ಮುನ್ನೆಚ್ಚರಿಕೆಗಳೇನು? / Precautions?", text: selectedLang === "kn-IN" ? "ಮಳೆಯಿಂದ ಬೆಳೆ ರಕ್ಷಣೆಗೆ ಮುನ್ನೆಚ್ಚರಿಕೆಗಳೇನು?" : "What precautions should I take before rain?" },
          ].map((prompt) => (
            <button
              key={prompt.label}
              type="button"
              onClick={() => setTextInput(prompt.text)}
              className="rounded-full border border-[#176B35]/20 bg-[#FAF9F2] hover:bg-mint px-3 py-1 text-[11px] font-medium text-deep transition"
            >
              {prompt.label}
            </button>
          ))}
        </div>

        <form onSubmit={handleSendText} className="flex gap-2 pt-2 border-t border-[#176B35]/10">
          <input
            className="rm-input"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder="Type or dictate a farming question..."
            disabled={loading}
          />
          <button type="submit" disabled={loading || !textInput.trim()} className="rm-btn-primary shrink-0">
            <Send className="h-4 w-4" />
            Send
          </button>
        </form>
      </div>
    </div>
  );
};
