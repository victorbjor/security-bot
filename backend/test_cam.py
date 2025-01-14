import cv2

camera = cv2.VideoCapture(0)  # Open the default webcam
if not camera.isOpened():
    print("Error: Could not access the webcam.")
    exit()

while True:
    success, frame = camera.read()
    if not success:
        print("Error: Failed to read frame.")
        break

    cv2.imshow("Webcam Feed", frame)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camera.release()
cv2.destroyAllWindows()