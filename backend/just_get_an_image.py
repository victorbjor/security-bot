import cv2
import base64

# Function to convert an image to a base64-encoded string
def frame_to_base64(frame):
    _, buffer = cv2.imencode('.jpg', frame)  # Encode the frame as a JPEG
    base64_string = base64.b64encode(buffer).decode('utf-8')  # Convert to base64
    return base64_string

def get_cam_image():
    camera = cv2.VideoCapture(0)  # Open the default webcam
    if not camera.isOpened():
        print("Error: Could not access the webcam.")
        return None

    last_frame = None

    # Capture 30 frames
    for _ in range(30):
        success, frame = camera.read()
        if not success:
            print("Error: Failed to read frame.")
            break

        last_frame = frame

    camera.release()

    # Convert the last captured frame to a base64 string
    if last_frame is not None:
        base64_image = frame_to_base64(last_frame)
        return base64_image
    else:
        print("No frame captured.")
        return None

