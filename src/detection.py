import cv2
from ultralytics import YOLO

def process_traffic_video(video_path):
    print("Loading YOLO model...")
    model = YOLO('yolov8n.pt') 
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file at {video_path}")
        return

    print("Processing video... Press 'q' to stop.")
    vehicle_classes = [2, 3, 5, 7]
    
    # --- NEW: Counting Variables ---
    vehicle_count = 0
    counted_ids = set() # Stores IDs of vehicles already counted
    
    # Define the Y-coordinate for our horizontal counting line
    # Note: You may need to change this number (e.g., 300, 500) depending on your video's resolution
    line_y = 350 
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("End of video stream.")
            break

        # Run YOLO tracking
        results = model.track(frame, persist=True, classes=vehicle_classes, conf=0.5, verbose=False)
        
        # --- NEW: Draw the counting line on the frame ---
        # Get the width of the video to draw the line all the way across
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        cv2.line(frame, (0, line_y), (width, line_y), (0, 0, 255), 3) # Red line, thickness 3
        
        # --- NEW: Counting Logic ---
        # Check if any objects were detected and have IDs assigned
        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()   # Bounding box coordinates
            track_ids = results[0].boxes.id.cpu().numpy() # Unique tracking IDs
            
            for box, track_id in zip(boxes, track_ids):
                x1, y1, x2, y2 = box
                
                # Calculate the center Y-coordinate of the bounding box
                cy = int((y1 + y2) / 2)
                
                # If the center crosses our line (within a 15-pixel margin) AND hasn't been counted yet
                if line_y - 15 < cy < line_y + 15 and track_id not in counted_ids:
                    vehicle_count += 1
                    counted_ids.add(track_id) # Mark this ID as counted
                    
        # Plot the bounding boxes onto the frame
        annotated_frame = results[0].plot()
        
        # --- NEW: Display the total count on the screen ---
        cv2.putText(annotated_frame, f"Total Vehicles: {vehicle_count}", (50, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2) # Green text

        # Display the frame
        cv2.imshow("Traffic Tracking & Counting", annotated_frame)

        if cv2.waitKey(25) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    video_file = "data/raw/test_video.mp4" 
    process_traffic_video(video_file)
