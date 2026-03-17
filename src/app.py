import streamlit as st
import cv2
import subprocess
from detection import TrafficDetector

# --- Page Configuration ---
st.set_page_config(page_title="Adaptive Traffic AI", layout="wide")
st.title("🚦 Adaptive Traffic Management Dashboard")

# --- Sidebar Controls ---
with st.sidebar:
    st.header("Control Panel")
    start_cameras = st.button("Start Camera Feeds", type="primary")
    stop_cameras = st.button("Stop Cameras")
    st.divider()
    
    # Launch Pygame simulation completely untouched in the background
    if st.button("Launch Pygame Simulation"):
        subprocess.Popen(["python", "src/simulation.py"])
        st.success("Simulation launched in native window!")

# --- Main Dashboard Layout ---
# Create 2 columns for the top row, 2 for the bottom
col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

# Placeholders for our video frames and metric counts
with col1:
    st.subheader("North Camera")
    count_n = st.empty()
    frame_n = st.empty()

with col2:
    st.subheader("East Camera")
    count_e = st.empty()
    frame_e = st.empty()

with col3:
    st.subheader("South Camera")
    count_s = st.empty()
    frame_s = st.empty()

with col4:
    st.subheader("West Camera")
    count_w = st.empty()
    frame_w = st.empty()

# --- Video Processing Loop ---
if start_cameras:
    # Initialize our AI Detector
    detector = TrafficDetector()
    
    # Path to your raw video (we use the same one 4 times for now)
    video_path = "data/raw/test_video.mp4" # UPDATE THIS if your file is named differently!
    
    caps = [cv2.VideoCapture(video_path) for _ in range(4)]
    
    while True:
        if stop_cameras:
            break
            
        frames = []
        for cap in caps:
            ret, frame = cap.read()
            if not ret:
                # If the video ends, loop it back to the start
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
            frames.append(frame)

        # Process each frame through YOLO
        processed_frames = []
        counts = []
        for frame in frames:
            # Resize frame to save processing power on the UI
            small_frame = cv2.resize(frame, (640, 360))
            proc_frame, count = detector.process_frame(small_frame)
            
            # Streamlit needs RGB, OpenCV uses BGR
            proc_frame_rgb = cv2.cvtColor(proc_frame, cv2.COLOR_BGR2RGB)
            processed_frames.append(proc_frame_rgb)
            counts.append(count)

        # Update the Streamlit UI placeholders
        count_n.metric("Vehicles in Queue", counts[0])
        frame_n.image(processed_frames[0], channels="RGB")
        
        count_e.metric("Vehicles in Queue", counts[1])
        frame_e.image(processed_frames[1], channels="RGB")
        
        count_s.metric("Vehicles in Queue", counts[2])
        frame_s.image(processed_frames[2], channels="RGB")
        
        count_w.metric("Vehicles in Queue", counts[3])
        frame_w.image(processed_frames[3], channels="RGB")

    # Cleanup
    for cap in caps:
        cap.release()


