import cv2
from cv2.typing import MatLike

def extract_first_frame(video_source: str, output_image_path = "first_frame.jpg") -> MatLike | None:
    """
    Extracts the first frame from a video file.

    Args:
        video_source (str): The path to the input video file (e.g., 'input_video.mp4').
        output_image_path (str): The path where the first frame will be saved 
                                 (e.g., 'first_frame.jpg').
    """
    # Open the video file
    cap = cv2.VideoCapture(video_source)

    # Check if the video was opened successfully
    if not cap.isOpened():
        print(f"Error: Could not open video at {video_source}")
        return None

    # Read the first frame. `ret` is a boolean, `frame` is the image data (numpy array).
    ret, frame = cap.read()

    # Release the video capture object to free resources
    cap.release()
    
    if ret:
        # Save the frame as an image
        cv2.imwrite(output_image_path, frame)
        print(f"Successfully extracted and saved the first frame to {output_image_path}")
        return frame  # Return the first frame as a NumPy array
    else:
        print("Error: Could not read the first frame.")
        return None

def load_video_frames(video_source: str):
    """Generator that yields frames from a video file."""
    cap = cv2.VideoCapture(video_source)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        yield frame
    cap.release()

if __name__ == "__main__":
    extract_first_frame('../data/sample_video1.mp4', 'output_frame.jpg')
