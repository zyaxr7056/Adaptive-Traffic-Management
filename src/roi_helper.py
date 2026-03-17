import cv2

points = []

def click_event(event, x, y, flags, params):
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append([x, y])
        print(f"Point clicked: [{x}, {y}]")
        cv2.circle(img, (x, y), 5, (0, 0, 255), -1)
        
        # Draw a line between the points
        if len(points) >= 2:
            cv2.line(img, tuple(points[-2]), tuple(points[-1]), (255, 0, 0), 2)
            
        # Draw the closing line if 4 points are clicked
        if len(points) == 4:
            cv2.line(img, tuple(points[3]), tuple(points[0]), (255, 0, 0), 2)
            print("\n--- COPY THIS LINE INTO detection.py ---")
            print(f"self.roi_pts = np.array({points}, np.int32)")
            
        cv2.imshow('Click 4 Points for ROI', img)

# Load your video
video_path = "data/raw/test_video.mp4"  # Make sure this matches your file
cap = cv2.VideoCapture(video_path)
ret, img = cap.read()
cap.release()

if ret:
    # Resize to match exactly what app.py sees
    img = cv2.resize(img, (640, 360))
    cv2.imshow('Click 4 Points for ROI', img)
    cv2.setMouseCallback('Click 4 Points for ROI', click_event)
    print("Click 4 corners to draw your box (e.g., Top-Left, Top-Right, Bottom-Right, Bottom-Left).")
    print("Press any key to close the window when done.")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
else:
    print("Error: Could not read the video file.")

