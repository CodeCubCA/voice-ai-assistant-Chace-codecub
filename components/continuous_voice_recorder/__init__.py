import os
import streamlit.components.v1 as components

# Create a _RELEASE constant
# Set to False to use development server, True to use production build
_RELEASE = False  # TEMPORARILY using dev mode for debugging

# Declare component
if not _RELEASE:
    _component_func = components.declare_component(
        "continuous_voice_recorder",
        url="http://localhost:3000",  # React dev server runs on 3000
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("continuous_voice_recorder", path=build_dir)


def continuous_voice_recorder(auto_start=False, silence_threshold=0.02, silence_duration=2.0, key=None):
    """
    Continuous voice recorder component with Voice Activity Detection.

    Parameters:
    -----------
    auto_start : bool
        If True, automatically starts recording when component loads
    silence_threshold : float
        Audio level threshold below which is considered silence (0.0 to 1.0)
    silence_duration : float
        Seconds of silence before stopping recording
    key : str
        Unique key for the component

    Returns:
    --------
    dict or None
        Audio data as base64 encoded string when recording stops, or None
    """
    component_value = _component_func(
        auto_start=auto_start,
        silence_threshold=silence_threshold,
        silence_duration=silence_duration,
        key=key,
        default=None
    )

    return component_value
