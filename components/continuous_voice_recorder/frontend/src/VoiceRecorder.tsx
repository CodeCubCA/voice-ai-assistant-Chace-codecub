import React, { useEffect, useRef, useState, useCallback } from "react"
import {
  Streamlit,
  withStreamlitConnection,
  ComponentProps,
} from "streamlit-component-lib"

interface VoiceRecorderProps extends ComponentProps {
  args: {
    auto_start: boolean
    silence_threshold: number
    silence_duration: number
  }
}

const ContinuousVoiceRecorder: React.FC<VoiceRecorderProps> = (props) => {
  const { auto_start = false, silence_threshold = 0.02, silence_duration = 2.0 } = props.args

  const [isRecording, setIsRecording] = useState(false)
  const [status, setStatus] = useState<string>("Ready")

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null)
  const animationFrameRef = useRef<number | null>(null)

  // Voice Activity Detection
  const checkAudioLevel = useCallback(() => {
    if (!analyserRef.current) return

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
    analyserRef.current.getByteFrequencyData(dataArray)

    // Calculate average volume
    const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length
    const normalizedLevel = average / 255

    // Check if audio level is below silence threshold
    if (normalizedLevel < silence_threshold) {
      // Start silence timer if not already started
      if (!silenceTimerRef.current) {
        silenceTimerRef.current = setTimeout(() => {
          stopRecording()
        }, silence_duration * 1000)
      }
    } else {
      // Reset silence timer if audio detected
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current)
        silenceTimerRef.current = null
      }
    }

    // Continue monitoring
    if (isRecording) {
      animationFrameRef.current = requestAnimationFrame(checkAudioLevel)
    }
  }, [isRecording, silence_threshold, silence_duration])

  // Start recording
  const startRecording = useCallback(async () => {
    try {
      setStatus("Requesting microphone access...")

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      })

      streamRef.current = stream

      // Set up audio context for VAD
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
      audioContextRef.current = audioContext

      const source = audioContext.createMediaStreamSource(stream)
      const analyser = audioContext.createAnalyser()
      analyser.fftSize = 2048
      analyserRef.current = analyser

      source.connect(analyser)

      // Set up media recorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: "audio/webm;codecs=opus"
      })

      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" })

        // Convert to base64
        const reader = new FileReader()
        reader.onloadend = () => {
          const base64data = reader.result as string
          // Send to Streamlit
          Streamlit.setComponentValue({
            audio: base64data,
            timestamp: Date.now()
          })
        }
        reader.readAsDataURL(audioBlob)

        audioChunksRef.current = []
      }

      mediaRecorder.start()
      setIsRecording(true)
      setStatus("🔴 Listening...")

      // Start VAD monitoring
      checkAudioLevel()

    } catch (error) {
      console.error("Error accessing microphone:", error)
      setStatus(`Error: ${error}`)
    }
  }, [checkAudioLevel])

  // Stop recording
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop()
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }

    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }

    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current)
      silenceTimerRef.current = null
    }

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
      animationFrameRef.current = null
    }

    setIsRecording(false)
    setStatus("Processing...")
  }, [])

  // Auto-start if requested
  useEffect(() => {
    if (auto_start && !isRecording) {
      // Small delay to ensure component is mounted
      setTimeout(() => {
        startRecording()
      }, 100)
    }
  }, [auto_start, startRecording, isRecording])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRecording()
    }
  }, [stopRecording])

  // Notify Streamlit that component is ready
  useEffect(() => {
    Streamlit.setFrameHeight(120)
  }, [])

  return (
    <div style={styles.container}>
      <div style={styles.statusBar}>
        <span style={styles.statusText}>{status}</span>
      </div>

      <div style={styles.controls}>
        {!isRecording ? (
          <button
            onClick={startRecording}
            style={{...styles.button, ...styles.startButton}}
          >
            🎤 Start Listening
          </button>
        ) : (
          <div style={styles.recordingIndicator}>
            <div style={styles.pulse} />
            <span style={styles.recordingText}>Listening (will stop on silence)</span>
          </div>
        )}
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>
    </div>
  )
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif",
    padding: "20px",
    backgroundColor: "#ffffff",
    borderRadius: "10px",
    boxShadow: "0 2px 10px rgba(0,0,0,0.1)",
  },
  statusBar: {
    marginBottom: "15px",
    textAlign: "center",
  },
  statusText: {
    fontSize: "14px",
    color: "#666",
    fontWeight: 500,
  },
  controls: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
  },
  button: {
    padding: "12px 24px",
    fontSize: "16px",
    fontWeight: 600,
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    transition: "all 0.2s",
  },
  startButton: {
    backgroundColor: "#4CAF50",
    color: "white",
  },
  recordingIndicator: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
  },
  pulse: {
    width: "12px",
    height: "12px",
    borderRadius: "50%",
    backgroundColor: "#f44336",
    animation: "pulse 1.5s ease-in-out infinite",
  },
  recordingText: {
    fontSize: "14px",
    color: "#f44336",
    fontWeight: 600,
  },
}

export default withStreamlitConnection(ContinuousVoiceRecorder)
