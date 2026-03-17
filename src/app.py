import streamlit as st
import cv2
from ultralytics import YOLO

# 1. Set up the page layout
st.set_page_config(page_title="Traffic Management System", layout="wide")
st.title("🚦 AI Traffic Management Dashboard")

@st.cache_resource
def load_model():
    return YOLO('yolov8n.pt')
    
model = load_model()

# --- NEW: Use Session State for Buttons ---
if "run_video" not in st.session_state:
    st.session_state.run_video = False

def start_video():
    st.session_state.run_video = True

def stop_video():
    st.session_state.run_video = False

st.sidebar.header("Controls")
# Bind the buttons to our state functions
st.sidebar.button("Start Video", on_click=start_video)
st.sidebar.button("Stop Video", on_click=stop_video)

# 2. Create the UI Layout
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("Live Traffic Feed")
    frame_placeholder = st.empty()

with col2:
    st.subheader("Traffic Stats")
    count_placeholder = st.empty()
    count_placeholder.metric(label="Total Vehicles Counted", value=0)

# 3. Processing Logic 
if st.session_state.run_video:
    # --- FIXED: Correct relative path from the root directory ---
    video_path = "data/raw/test_video.mp4" 
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        st.error(f"Error: Could not open video file at {video_path}. Please check the path.")
    else:
        vehicle_classes = [2, 3, 5, 7]
        vehicle_count = 0
        counted_ids = set()
        line_y = 350 
        
        # Loop runs as long as there are frames AND the stop button hasn't been clicked
        while cap.isOpened() and st.session_state.run_video:
            ret, frame = cap.read()
            if not ret:
                st.sidebar.info("Video finished.")
                st.session_state.run_video = False
                break
                
            results = model.track(frame, persist=True, classes=vehicle_classes, conf=0.5, verbose=False)
            
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            cv2.line(frame, (0, line_y), (width, line_y), (0, 0, 255), 3)
            
            if results[0].boxes.id is not None:
                boxes = results[0].boxes.xyxy.cpu().numpy()
                track_ids = results[0].boxes.id.cpu().numpy()
                
                for box, track_id in zip(boxes, track_ids):
                    x1, y1, x2, y2 = box
                    cy = int((y1 + y2) / 2)
                    
                    if line_y - 15 < cy < line_y + 15 and track_id not in counted_ids:
                        vehicle_count += 1
                        counted_ids.add(track_id)
            
            annotated_frame = results[0].plot()
            annotated_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            
            frame_placeholder.image(annotated_frame, channels="RGB", width="stretch")
            count_placeholder.metric(label="Total Vehicles Counted", value=vehicle_count)
            
        cap.release()


