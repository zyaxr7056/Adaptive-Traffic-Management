import streamlit as st
import cv2
import subprocess
import sys
import os
import tempfile
import pandas as pd
from detection import TrafficDetector

# --- Page Configuration ---
st.set_page_config(page_title="Adaptive Traffic AI", layout="wide")
st.title("Adaptive Traffic Management Dashboard")

# --- Sidebar Controls ---
with st.sidebar:
    st.header("Control Panel")
    
    # Model Selector
    model_choice = st.selectbox(
        "AI Detection Model", 
        ["Custom Tuned (Traffic)", "Pre-trained (COCO Base)"]
    )
    
    start_cameras = st.button("Start Camera Feeds", type="primary")
    stop_cameras = st.button("Stop Cameras")
    st.divider()

    # Launch Pygame simulation in the background
    if st.button("Launch Pygame Simulation"):
        subprocess.Popen([sys.executable, "src/simulation.py"])
        st.success("Simulation launched in native window!")

# --- Tab Layout ---
tab_live, tab_raw, tab_analytics = st.tabs(["Live Feeds", "Raw Data", "Analytics"])

# --- Live Feeds Tab ---
with tab_live:
    st.subheader("Camera Video Uploads")

    # File uploaders for each camera direction
    upload_col1, upload_col2 = st.columns(2)
    upload_col3, upload_col4 = st.columns(2)

    with upload_col1:
        north_video = st.file_uploader("North Camera (MP4)", type=["mp4"], key="north")
    with upload_col2:
        east_video = st.file_uploader("East Camera (MP4)", type=["mp4"], key="east")
    with upload_col3:
        south_video = st.file_uploader("South Camera (MP4)", type=["mp4"], key="south")
    with upload_col4:
        west_video = st.file_uploader("West Camera (MP4)", type=["mp4"], key="west")

    st.divider()

    # Create 2x2 grid for video frames
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

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

# --- Raw Data Tab ---
with tab_raw:
    st.subheader("Simulation Results Data")

    csv_path = "data/simulation_results.csv"

    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        st.dataframe(df, use_container_width=True)

        # Download button
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name="simulation_results.csv",
            mime="text/csv"
        )
    else:
        st.info("No simulation data available yet. Run a simulation to generate data.")

# --- Analytics Tab ---
with tab_analytics:
    st.subheader("Simulation Analytics")

    csv_path = "data/simulation_results.csv"

    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)

        # Summary metrics
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric("Total Simulations", len(df))
        with metric_col2:
            st.metric("Avg Vehicles/Sim", f"{df['Total'].mean():.1f}")
        with metric_col3:
            st.metric("Max Vehicles", df['Total'].max())

        st.divider()

        # Line chart of total vehicles per simulation run
        st.subheader("Total Vehicles Passed Per Simulation")

        # Create a run index for x-axis
        chart_data = df[['Total']].copy()
        chart_data['Run'] = range(1, len(chart_data) + 1)
        chart_data = chart_data.set_index('Run')

        st.line_chart(chart_data)

        # Lane breakdown chart
        st.subheader("Vehicles by Lane Per Simulation")
        lane_data = df[['Lane 1 (N)', 'Lane 2 (E)', 'Lane 3 (S)', 'Lane 4 (W)']].copy()
        lane_data['Run'] = range(1, len(lane_data) + 1)
        lane_data = lane_data.set_index('Run')

        st.line_chart(lane_data)
    else:
        st.info("No simulation data available yet. Run a simulation to generate analytics.")

# --- Video Processing Loop ---
if start_cameras:
    # Save uploaded files to temp directory and collect paths
    video_paths = []
    temp_dir = tempfile.mkdtemp()

    uploaded_files = [north_video, east_video, south_video, west_video]
    directions = ['north', 'east', 'south', 'west']

    for uploaded_file, direction in zip(uploaded_files, directions):
        if uploaded_file is not None:
            # Save to temp file
            temp_path = os.path.join(temp_dir, f"{direction}.mp4")
            with open(temp_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            video_paths.append(temp_path)
        else:
            # Fallback to default video if no upload
            default_path = "data/raw/test_video.mp4"
            video_paths.append(default_path)

    # Check if we have valid paths
    valid_paths = all(os.path.exists(p) for p in video_paths)

    if not valid_paths:
        st.error("Please upload video files for all cameras or ensure default video exists.")
    else:
        # Determine which weights to load based on user selection
        if model_choice == "Custom Tuned (Traffic)":
            weight_path = "models/best.pt"
        else:
            weight_path = "yolov8n.pt"
            
        # Initialize AI Detector with chosen weights
        detector = TrafficDetector(model_path=weight_path)

        # Open video captures
        caps = [cv2.VideoCapture(path) for path in video_paths]

        while True:
            if stop_cameras:
                break

            frames = []
            for cap in caps:
                ret, frame = cap.read()
                if not ret:
                    # Loop video back to start
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()
                if frame is not None:
                    frames.append(frame)
                else:
                    frames.append(None)

            # Skip if any frame is invalid
            if any(frame is None for frame in frames):
                continue

            # Process each frame through YOLO
            processed_frames = []
            counts = []
            for frame in frames:
                small_frame = cv2.resize(frame, (640, 360))
                proc_frame, count = detector.process_frame(small_frame)
                proc_frame_rgb = cv2.cvtColor(proc_frame, cv2.COLOR_BGR2RGB)
                processed_frames.append(proc_frame_rgb)
                counts.append(count)

            # Update UI placeholders
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
