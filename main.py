from flask import Flask
from flask import Response,render_template
import threading
import cv2
import pyautogui
from time import time
from math import hypot
import mediapipe as mp
import matplotlib.pyplot as plt
import threading
# import time


# from imutils.video import VideoStream
# from game_model import *

# outputFrame = None
# lock = threading.Lock()

# Initialize mediapipe pose class.
mp_pose = mp.solutions.pose

# Setup the Pose function for images.
pose_image = mp_pose.Pose(static_image_mode=True,
                          min_detection_confidence=0.5, model_complexity=1)

# Setup the Pose function for videos.
pose_video = mp_pose.Pose(static_image_mode=False, model_complexity=1, min_detection_confidence=0.7,
                          min_tracking_confidence=0.7)

# Initialize mediapipe drawing class.
mp_drawing = mp.solutions.drawing_utils


# FUNCTION TO DETECT POSE

def detectPose(image, pose, draw=False, display=False):
    '''
    This function performs the pose detection on the most prominent person in an image.
    Args:
        image:   The input image with a prominent person whose pose landmarks needs to be detected.
        pose:    The pose function required to perform the pose detection.
        draw:    A boolean value that is if set to true the function draw pose landmarks on the output image. 
        display: A boolean value that is if set to true the function displays the original input image, and the 
                 resultant image and returns nothing.
    Returns:
        output_image: The input image with the detected pose landmarks drawn if it was specified.
        results:      The output of the pose landmarks detection on the input image.
    '''

    # Create a copy of the input image.
    output_image = image.copy()

    # Convert the image from BGR into RGB format.
    imageRGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Perform the Pose Detection.
    results = pose.process(imageRGB)

    # Check if any landmarks are detected and are specified to be drawn.
    if results.pose_landmarks and draw:

        # Draw Pose Landmarks on the output image.
        mp_drawing.draw_landmarks(image=output_image, landmark_list=results.pose_landmarks,
                                  connections=mp_pose.POSE_CONNECTIONS,
                                  landmark_drawing_spec=mp_drawing.DrawingSpec(color=(255, 255, 255),
                                                                               thickness=3, circle_radius=3),
                                  connection_drawing_spec=mp_drawing.DrawingSpec(color=(49, 125, 237),
                                                                                 thickness=2, circle_radius=2))

    # Check if the original input image and the resultant image are specified to be displayed.
    if display:

        # Display the original input image and the resultant image.
        plt.figure(figsize=[22, 22])
        plt.subplot(121)
        plt.imshow(image[:, :, ::-1])
        plt.title("Original Image")
        plt.axis('off')
        plt.subplot(122)
        plt.imshow(output_image[:, :, ::-1])
        plt.title("Output Image")
        plt.axis('off')

    # Otherwise
    else:

        # Return the output image and the results of pose landmarks detection.
        return output_image, results


# FUCNTION FOR STARTING
def checkHandsJoined(image, results, draw=False, display=False):
    '''
    This function checks whether the hands of the person are joined or not in an image.
    Args:
        image:   The input image with a prominent person whose hands status (joined or not) needs to be classified.
        results: The output of the pose landmarks detection on the input image.
        draw:    A boolean value that is if set to true the function writes the hands status & distance on the output image. 
        display: A boolean value that is if set to true the function displays the resultant image and returns nothing.
    Returns:
        output_image: The same input image but with the classified hands status written, if it was specified.
        hand_status:  The classified status of the hands whether they are joined or not.
    '''

    # Get the height and width of the input image.
    height, width, _ = image.shape

    # Create a copy of the input image to write the hands status label on.
    output_image = image.copy()

    # Get the left wrist landmark x and y coordinates.
    left_wrist_landmark = (results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST].x * width,
                           results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST].y * height)

    # Get the right wrist landmark x and y coordinates.
    right_wrist_landmark = (results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST].x * width,
                            results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST].y * height)

    # Calculate the euclidean distance between the left and right wrist.
    euclidean_distance = int(hypot(left_wrist_landmark[0] - right_wrist_landmark[0],
                                   left_wrist_landmark[1] - right_wrist_landmark[1]))

    # Compare the distance between the wrists with a appropriate threshold to check if both hands are joined.
    if euclidean_distance < 130:

        # Set the hands status to joined.
        hand_status = 'Hands Joined'

        # Set the color value to green.
        color = (0, 255, 0)

    # Otherwise.
    else:

        # Set the hands status to not joined.
        hand_status = 'Hands Not Joined'

        # Set the color value to red.
        color = (0, 0, 255)

    # Check if the Hands Joined status and hands distance are specified to be written on the output image.
    if draw:

        # Write the classified hands status on the image.
        cv2.putText(output_image, hand_status, (10, 30),
                    cv2.FONT_HERSHEY_PLAIN, 2, color, 3)

        # Write the the distance between the wrists on the image.
        cv2.putText(output_image, f'Distance: {euclidean_distance}', (10, 70),
                    cv2.FONT_HERSHEY_PLAIN, 2, color, 3)

    # Check if the output image is specified to be displayed.
    if display:

        # Display the output image.
        plt.figure(figsize=[10, 10])
        plt.imshow(output_image[:, :, ::-1])
        plt.title("Output Image")
        plt.axis('off')

    # Otherwise
    else:

        # Return the output image and the classified hands status indicating whether the hands are joined or not.
        return output_image, hand_status


# FUCNTION FOR LEFT AND RIGHT MOVEMENT
def checkLeftRight(image, results, draw=False, display=False):
    '''
    This function finds the horizontal position (left, center, right) of the person in an image.
    Args:
        image:   The input image with a prominent person whose the horizontal position needs to be found.
        results: The output of the pose landmarks detection on the input image.
        draw:    A boolean value that is if set to true the function writes the horizontal position on the output image. 
        display: A boolean value that is if set to true the function displays the resultant image and returns nothing.
    Returns:
        output_image:         The same input image but with the horizontal position written, if it was specified.
        horizontal_position:  The horizontal position (left, center, right) of the person in the input image.
    '''

    # Declare a variable to store the horizontal position (left, center, right) of the person.
    horizontal_position = None

    # Get the height and width of the image.
    height, width, _ = image.shape

    # Create a copy of the input image to write the horizontal position on.
    output_image = image.copy()

    # Retreive the x-coordinate of the left shoulder landmark.
    left_x = int(
        results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].x * width)

    # Retreive the x-corrdinate of the right shoulder landmark.
    right_x = int(
        results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].x * width)

    # Check if the person is at left that is when both shoulder landmarks x-corrdinates
    # are less than or equal to the x-corrdinate of the center of the image.
    if (right_x <= width//2 and left_x <= width//2):

        # Set the person's position to left.
        horizontal_position = 'Left'

    # Check if the person is at right that is when both shoulder landmarks x-corrdinates
    # are greater than or equal to the x-corrdinate of the center of the image.
    elif (right_x >= width//2 and left_x >= width//2):

        # Set the person's position to right.
        horizontal_position = 'Right'

    # Check if the person is at center that is when right shoulder landmark x-corrdinate is greater than or equal to
    # and left shoulder landmark x-corrdinate is less than or equal to the x-corrdinate of the center of the image.
    elif (right_x >= width//2 and left_x <= width//2):

        # Set the person's position to center.
        horizontal_position = 'Center'

    # Check if the person's horizontal position and a line at the center of the image is specified to be drawn.
    if draw:

        # Write the horizontal position of the person on the image.
        cv2.putText(output_image, horizontal_position, (5, height - 10),
                    cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 3)

        # Draw a line at the center of the image.
        cv2.line(output_image, (width//2, 0),
                 (width//2, height), (255, 255, 255), 2)

    # Check if the output image is specified to be displayed.
    if display:

        # Display the output image.
        plt.figure(figsize=[10, 10])
        plt.imshow(output_image[:, :, ::-1])
        plt.title("Output Image")
        plt.axis('off')

    # Otherwise
    else:

        # Return the output image and the person's horizontal position.
        return output_image, horizontal_position


# FUNCTION FOR UP AND DOWN MOVEMENT
def checkJumpCrouch(image, results, MID_Y=250, draw=False, display=False):
    '''
    This function checks the posture (Jumping, Crouching or Standing) of the person in an image.
    Args:
        image:   The input image with a prominent person whose the posture needs to be checked.
        results: The output of the pose landmarks detection on the input image.
        MID_Y:   The intial center y-coordinate of both shoulders landmarks of the person recorded during starting
                 the game. This will give the idea of the person's height when he is standing straight.
        draw:    A boolean value that is if set to true the function writes the posture on the output image. 
        display: A boolean value that is if set to true the function displays the resultant image and returns nothing.
    Returns:
        output_image: The input image with the person's posture written, if it was specified.
        posture:      The posture (Jumping, Crouching or Standing) of the person in an image.
    '''

    # Get the height and width of the image.
    height, width, _ = image.shape

    # Create a copy of the input image to write the posture label on.
    output_image = image.copy()

    # Retreive the y-coordinate of the left shoulder landmark.
    left_y = int(
        results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].y * height)

    # Retreive the y-coordinate of the right shoulder landmark.
    right_y = int(
        results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].y * height)

    # Calculate the y-coordinate of the mid-point of both shoulders.
    actual_mid_y = abs(right_y + left_y) // 2

    # Calculate the upper and lower bounds of the threshold.
    lower_bound = MID_Y-15
    upper_bound = MID_Y+100

    # Check if the person has jumped that is when the y-coordinate of the mid-point
    # of both shoulders is less than the lower bound.
    if (actual_mid_y < lower_bound):

        # Set the posture to jumping.
        posture = 'Jumping'

    # Check if the person has crouched that is when the y-coordinate of the mid-point
    # of both shoulders is greater than the upper bound.
    elif (actual_mid_y > upper_bound):

        # Set the posture to crouching.
        posture = 'Crouching'

    # Otherwise the person is standing and the y-coordinate of the mid-point
    # of both shoulders is between the upper and lower bounds.
    else:

        # Set the posture to Standing straight.
        posture = 'Standing'

    # Check if the posture and a horizontal line at the threshold is specified to be drawn.
    if draw:

        # Write the posture of the person on the image.
        cv2.putText(output_image, posture, (5, height - 50),
                    cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 3)

        # Draw a line at the intial center y-coordinate of the person (threshold).
        cv2.line(output_image, (0, MID_Y), (width, MID_Y), (255, 255, 255), 2)

    # Check if the output image is specified to be displayed.
    if display:

        # Display the output image.
        plt.figure(figsize=[10, 10])
        plt.imshow(output_image[:, :, ::-1])
        plt.title("Output Image")
        plt.axis('off')

    # Otherwise
    else:

        # Return the output image and posture indicating whether the person is standing straight or has jumped, or crouched.
        return output_image, posture

# def generate():
# 	# grab global references to the output frame and lock variables
# 	global outputFrame, lock
# 	# loop over frames from the output stream
# 	while True:
# 		# wait until the lock is acquired
# 		with lock:
# 			# check if the output frame is available, otherwise skip
# 			# the iteration of the loop
# 			if outputFrame is None:
# 				continue
# 			# encode the frame in JPEG format
# 			(flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
# 			# ensure the frame was successfully encoded
# 			if not flag:
# 				continue
# 		# yield the output frame in the byte format
# 		yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
# 			bytearray(encodedImage) + b'\r\n')

app = Flask(__name__)

# vs = VideoStream(src=0).start()
# time.sleep(2.0)

@app.route("/flask" , methods=['GET'])
def index():
	# RUNNING MAIN PROGRAM
    # Initialize the VideoCapture object to read from the webcam.
    camera_video = cv2.VideoCapture(0)
    camera_video.set(3, 1280)
    camera_video.set(4, 960)

    # Create named window for resizing purposes.
    # cv2.namedWindow('Subway Surfers with Pose Detection', cv2.WINDOW_NORMAL)

    # Initialize a variable to store the time of the previous frame.
    time1 = 0

    # Initialize a variable to store the state of the game (started or not).
    game_started = False

    # Initialize a variable to store the index of the current horizontal position of the person.
    # At Start the character is at center so the index is 1 and it can move left (value 0) and right (value 2).
    x_pos_index = 1

    # Initialize a variable to store the index of the current vertical posture of the person.
    # At Start the person is standing so the index is 1 and he can crouch (value 0) and jump (value 2).
    y_pos_index = 1

    # Declate a variable to store the intial y-coordinate of the mid-point of both shoulders of the person.
    MID_Y = None

    # Initialize a counter to store count of the number of consecutive frames with person's hands joined.
    counter = 0

    # Initialize the number of consecutive frames on which we want to check if person hands joined before starting the game.
    num_of_frames = 10

    # outputFrame = None
    # lock = threading.Lock()

    # Iterate until the webcam is accessed successfully.
    while camera_video.isOpened():

        # Read a frame.
        ok, frame = camera_video.read()
        print(ok)
        print(frame)
        # Check if frame is not read properly then continue to the next iteration to read the next frame.
        if not ok:
            print("frame not read properly")
            continue
        print("frame read properly")
        # Flip the frame horizontally for natural (selfie-view) visualization.
        frame = cv2.flip(frame, 1)

        # Get the height and width of the frame of the webcam video.
        frame_height, frame_width, _ = frame.shape

        # Perform the pose detection on the frame.
        frame, results = detectPose(frame, pose_video, draw=game_started)

        # Check if the pose landmarks in the frame are detected.
        if results.pose_landmarks:

            # Check if the game has started
            if game_started:

                # Commands to control the horizontal movements of the character.
                # --------------------------------------------------------------------------------------------------------------

                # Get horizontal position of the person in the frame.
                frame, horizontal_position = checkLeftRight(
                    frame, results, draw=True)

                # Check if the person has moved to left from center or to center from right.
                if (horizontal_position == 'Left' and x_pos_index != 0) or (horizontal_position == 'Center' and x_pos_index == 2):

                    # Press the left arrow key.
                    pyautogui.press('left')

                    # Update the horizontal position index of the character.
                    x_pos_index -= 1

                # Check if the person has moved to Right from center or to center from left.
                elif (horizontal_position == 'Right' and x_pos_index != 2) or (horizontal_position == 'Center' and x_pos_index == 0):

                    # Press the right arrow key.
                    pyautogui.press('right')

                    # Update the horizontal position index of the character.
                    x_pos_index += 1

                # --------------------------------------------------------------------------------------------------------------

            # Otherwise if the game has not started
            else:

                # Write the text representing the way to start the game on the frame.
                cv2.putText(frame, 'JOIN BOTH HANDS TO START THE GAME.', (5, frame_height - 10), cv2.FONT_HERSHEY_PLAIN,
                            2, (0, 255, 0), 3)

            # Command to Start or resume the game.
            # ------------------------------------------------------------------------------------------------------------------

            # Check if the left and right hands are joined.
            if checkHandsJoined(frame, results)[1] == 'Hands Joined':

                # Increment the count of consecutive frames with +ve condition.
                counter += 1

                # Check if the counter is equal to the required number of consecutive frames.
                if counter == num_of_frames:

                    # Command to Start the game first time.
                    # ----------------------------------------------------------------------------------------------------------

                    # Check if the game has not started yet.
                    if not(game_started):

                        # Update the value of the variable that stores the game state.
                        game_started = True

                        # Retreive the y-coordinate of the left shoulder landmark.
                        left_y = int(
                            results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].y * frame_height)

                        # Retreive the y-coordinate of the right shoulder landmark.
                        right_y = int(
                            results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].y * frame_height)

                        # Calculate the intial y-coordinate of the mid-point of both shoulders of the person.
                        MID_Y = abs(right_y + left_y) // 2

                        # Move to 1300, 800, then click the left mouse button to start the game.
                        pyautogui.click(x=1300, y=800, button='left')

                    # ----------------------------------------------------------------------------------------------------------

                    # Command to resume the game after death of the character.
                    # ----------------------------------------------------------------------------------------------------------

                    # Otherwise if the game has started.
                    else:

                        # Press the space key.
                        pyautogui.press('space')

                    # ----------------------------------------------------------------------------------------------------------

                    # Update the counter value to zero.
                    counter = 0

            # Otherwise if the left and right hands are not joined.
            else:

                # Update the counter value to zero.
                counter = 0

            # ------------------------------------------------------------------------------------------------------------------

            # Commands to control the vertical movements of the character.
            # ------------------------------------------------------------------------------------------------------------------

            # Check if the intial y-coordinate of the mid-point of both shoulders of the person has a value.
            if MID_Y:

                # Get posture (jumping, crouching or standing) of the person in the frame.
                frame, posture = checkJumpCrouch(frame, results, MID_Y, draw=True)

                # Check if the person has jumped.
                if posture == 'Jumping' and y_pos_index == 1:

                    # Press the up arrow key
                    pyautogui.press('up')

                    # Update the veritcal position index of  the character.
                    y_pos_index += 1

                # Check if the person has crouched.
                elif posture == 'Crouching' and y_pos_index == 1:

                    # Press the down arrow key
                    pyautogui.press('down')

                    # Update the veritcal position index of the character.
                    y_pos_index -= 1

                # Check if the person has stood.
                elif posture == 'Standing' and y_pos_index != 1:

                    # Update the veritcal position index of the character.
                    y_pos_index = 1

            # ------------------------------------------------------------------------------------------------------------------

        # Otherwise if the pose landmarks in the frame are not detected.
        else:

            # Update the counter value to zero.
            counter = 0

        # Calculate the frames updates in one second
        # ----------------------------------------------------------------------------------------------------------------------

        # Set the time for this frame to the current time.
        time2 = time()

        # Check if the difference between the previous and this frame time > 0 to avoid division by zero.
        if (time2 - time1) > 0:

            # Calculate the number of frames per second.
            frames_per_second = 1.0 / (time2 - time1)

            # Write the calculated number of frames per second on the frame.
            cv2.putText(frame, 'FPS: {}'.format(int(frames_per_second)),
                        (10, 30), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 3)

        # Update the previous frame time to this frame time.
        # As this frame will become previous frame in next iteration.
        time1 = time2

        # ----------------------------------------------------------------------------------------------------------------------

        # Display the frame.
        cv2.imshow('Play Game', frame)
    #     with lock:
    # 	    outputFrame = frame.copy()

        # Wait for 1ms. If a a key is pressed, retreive the ASCII code of the key.
        k = cv2.waitKey(1) & 0xFF


        # Check if 'ESC' is pressed and break the loop.
        if(k == 27):
            game_started = False
            break

        return frame

    # Release the VideoCapture Object and close the windows.
    camera_video.release()
    cv2.destroyAllWindows()

# def index():
    
#     return "Flask Server"

if __name__ == "__main__" :
    app.run(port=5000,debug=True)

# vs.stop()