import io
import json
import os
import warnings
import requests

import matplotlib.pyplot as plt
from matplotlib import patches
from PIL import Image

from roboflow.config import OBJECT_DETECTION_MODEL, PREDICTION_OBJECT, CLASSIFICATION_MODEL
from roboflow.util.image_utils import check_image_url


def exception_check(image_path_check=None):
    # Check if Image path exists exception check (for both hosted URL and local image)
    if image_path_check is not None:
        if not os.path.exists(image_path_check) and not check_image_url(image_path_check):
            raise Exception("Image does not exist at " + image_path_check + "!")


def plot_image(image_path):
    """
    Helper method to plot image

    :param image_path: path of image to be plotted (can be hosted or local)
    :return:
    """
    # Exception to check if image path exists
    exception_check(image_path_check=image_path)
    # Try opening local image
    try:
        img = Image.open(image_path)
    except OSError:
        # Try opening Hosted image
        response = requests.get(image_path)
        img = Image.open(io.BytesIO(response.content))
    # Plot image axes
    figure, axes = plt.subplots()
    axes.imshow(img)
    return figure, axes


def plot_annotation(axes, prediction=None, stroke=1):
    """
    Helper method to plot annotations

    :param axes:
    :param prediction:
    :return:
    """
    # Object Detection annotation
    if prediction['prediction_type'] == OBJECT_DETECTION_MODEL:
        # Get height, width, and center coordinates of prediction
        if prediction is not None:
            height = prediction['height']
            width = prediction['width']
            x = prediction['x']
            y = prediction['y']
            rect = patches.Rectangle((x - width / 2, y - height / 2), width, height,
                                     linewidth=stroke, edgecolor='r', facecolor='none')
            # Plot Rectangle
            axes.add_patch(rect)
    elif prediction['prediction_type'] == CLASSIFICATION_MODEL:
        axes.set_title('Class: ' + prediction['top'] + " | Confidence: " + prediction['confidence'])


class Prediction:
    def __init__(self, json_prediction, image_path, prediction_type=OBJECT_DETECTION_MODEL):
        """
        Generalized Prediction for both Object Detection and Classification Models

        :param json_prediction:
        :param image_path:
        """
        # Set image path in JSON prediction
        json_prediction['image_path'] = image_path
        json_prediction['prediction_type'] = prediction_type
        self.json_prediction = json_prediction

    def json(self):
        return self.json_prediction

    def plot(self, stroke=1):
        # Exception to check if image path exists
        exception_check(image_path_check=self['image_path'])
        figure, axes = plot_image(self['image_path'])

        plot_annotation(axes, self, stroke)
        plt.show()

    def save(self, path='predictions.jpg'):
        if self['prediction_type'] == OBJECT_DETECTION_MODEL:
            pass
        elif self['prediction_type'] == CLASSIFICATION_MODEL:
            pass

    def __str__(self) -> str:
        """
        :return: JSON formatted string of prediction
        """
        # Pretty print the JSON prediction as a String
        prediction_string = json.dumps(self.json_prediction, indent=2)
        return prediction_string

    def __getitem__(self, key):
        """

        :param key:
        :return:
        """
        # Allows the prediction to be accessed like a dictionary
        return self.json_prediction[key]

    # Make representation equal to string value
    __repr__ = __str__


class PredictionGroup:
    def __init__(self, *args):
        """
        :param args: The prediction(s) to be added to the prediction group
        """
        # List of predictions (core of the PredictionGroup)
        self.predictions = []
        # Base image path (path of image of first prediction in prediction group)
        self.base_image_path = ''
        # Base prediction type (prediction type of image of first prediction in prediction group)
        self.base_prediction_type = ''
        # Iterate through the arguments
        for index, prediction in enumerate(args):
            # Set base image path based on first prediction
            if index == 0:
                self.base_image_path = prediction['image_path']
                self.base_prediction_type = prediction['prediction_type']
            # If not a Prediction object then do not allow into the prediction group
            self.__exception_check(is_prediction_check=prediction)
            # Add prediction to prediction group otherwise
            self.predictions.append(prediction)

    def add_prediction(self, prediction=None):
        """

        :param prediction: Prediction to add to the prediction group
        """
        # If not a Prediction object then do not allow into the prediction group
        # Also checks if prediction types are the same (i.e. object detection predictions in object detection groups)
        self.__exception_check(is_prediction_check=prediction, prediction_type_check=prediction['prediction_type'])
        # If there is more than one prediction and the prediction image path is
        # not the group image path then warn user
        if self.__len__() > 0:
            self.__exception_check(image_path_check=prediction['image_path'])
        # If the prediction group is empty, make the base image path of the prediction
        elif self.__len__() == 0:
            self.base_image_path = prediction['image_path']
        # Append prediction to group
        self.predictions.append(prediction)

    def plot(self, stroke=1):
        if len(self) > 0:
            # Check if image path exists
            exception_check(image_path_check=self.base_image_path)
            # Plot image if image path exists
            figure, axes = plot_image(self.base_image_path)
            # Plot annotations in prediction group
            for single_prediction in self:
                plot_annotation(axes, single_prediction, stroke)

        plt.show()

    def save(self, path="predictions.jpg"):
        # TODO: Implement save to save prediction as a image
        if self['prediction_type'] == OBJECT_DETECTION_MODEL:
            pass
        elif self['prediction_type'] == CLASSIFICATION_MODEL:
            pass

    def __str__(self):
        """

        :return:
        """
        # final string to be returned for the prediction group
        prediction_group_string = ""
        # Iterate through the predictions and convert each prediction into a string format
        for prediction in self.predictions:
            prediction_group_string += str(prediction) + "\n\n"
        # return the prediction group string
        return prediction_group_string

    def __getitem__(self, index):
        # Allows prediction group to be accessed via an index
        return self.predictions[index]

    def __len__(self):
        # Length of prediction based off of number of predictions
        return len(self.predictions)

    def __exception_check(self, is_prediction_check=None, image_path_check=None, prediction_type_check=None):
        # Ensures only predictions can be added to a prediction group
        if is_prediction_check is not None:
            if type(is_prediction_check).__name__ is not PREDICTION_OBJECT:
                raise Exception("Cannot add type " + type(is_prediction_check).__name__ + " to PredictionGroup")

        # Warns user if predictions have different prediction types
        if prediction_type_check is not None:
            if self.__len__() > 0 and prediction_type_check != self.base_prediction_type:
                warnings.warn(
                    "This prediction is a different type (" + prediction_type_check +
                    ") than the prediction group base type (" + self.base_prediction_type +
                    ")")

        # Gives user warning that base path is not equal to image path
        if image_path_check is not None:
            if self.base_image_path != image_path_check:
                warnings.warn(
                    "This prediction has a different image path (" + image_path_check +
                    ") than the prediction group base image path (" + self.base_image_path +
                    ")")

    @staticmethod
    def create_prediction_group(json_response, image_path, prediction_type):
        """

        :param prediction_type:
        :param json_response: Based on Roboflow JSON Response from Inference API
        :param model:
        :param image_path:
        :return:
        """
        prediction_list = []
        for prediction in json_response['predictions']:
            prediction = Prediction(prediction, image_path, prediction_type=prediction_type)
            prediction_list.append(prediction)

        return PredictionGroup(*prediction_list)