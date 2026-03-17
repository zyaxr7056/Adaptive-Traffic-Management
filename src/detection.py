import cv2
import numpy as np
from ultralytics import YOLO

class TrafficDetector:
    def __init__(self, model_path='yolov8n.pt'):
        # Load the YOLOv8 model
        self.model = YOLO(model_path)
        
        # Define a placeholder Region of Interest (ROI) polygon.
        # We will need to adjust these coordinates later to match your actual road!
        self.roi_pts = np.array([[237, 10], [440, 11], [632, 352], [2, 273]], np.int32)
        self.roi_pts = self.roi_pts.reshape((-1, 1, 2))

    def process_frame(self, frame):
        # Run YOLO inference (filtering for classes: 2=car, 3=motorcycle, 5=bus, 7=truck)
        results = self.model(frame, classes=[2, 3, 5, 7], verbose=False)
        
        vehicles_in_roi = 0
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                # Get bounding box coordinates
                x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                
                # Calculate the center point of the vehicle
                cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
                
                # Check if the center point is strictly inside our defined ROI polygon
                is_inside = cv2.pointPolygonTest(self.roi_pts, (cx, cy), False)
                
                if is_inside >= 0:
                    vehicles_in_roi += 1
                    # Draw a green dot and green box if it's in the queue
                    cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                else:
                    # Draw a red dot if it's outside the queue
                    cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
                    
        # Draw the ROI polygon on the frame so we can see it
        cv2.polylines(frame, [self.roi_pts], isClosed=True, color=(255, 0, 0), thickness=2)
        
        return frame, vehicles_in_roi
