import React from "react"
import { createRoot } from "react-dom/client"
import ContinuousVoiceRecorder from "./VoiceRecorder"

const container = document.getElementById("root")
if (container) {
  const root = createRoot(container)
  root.render(
    <React.StrictMode>
      <ContinuousVoiceRecorder />
    </React.StrictMode>
  )
}
