<div align="center" markdown>
<img src="https://github.com/user-attachments/assets/1f2782b2-7eda-43fa-8368-af794f0782ee"/>  

# Real-time Labeling Quality Check

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#Avaiable actions">Avaiable actions</a> •
  <a href="#Available checks">Available checks</a> •
  <a href="#How-To-Run">How To Run</a> •
  <a href="#Using the results">Using the results</a>
</p>

[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](../../../../supervisely-ecosystem/real-time-labeling-quality-check)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervisely.com/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/real-time-labeling-quality-check)
[![views](https://app.supervisely.com/img/badges/views/supervisely-ecosystem/real-time-labeling-quality-check.png)](https://supervisely.com)
[![runs](https://app.supervisely.com/img/badges/runs/supervisely-ecosystem/real-time-labeling-quality-check.png)](https://supervisely.com)

</div>

# Overview
This application is designed to be an assistant for data labeling. It helps to find incorrect labels by predefined rules and highlight them in different ways. For example: show simple notification in the Labeling Tool, create a new issue with detailed report or even automatically reject the image if working in the [Labeling Queue](https://supervisely.com/blog/labeling-queues/).<br>

# Avaiable actions
By default the application will show a notification in the Labeling Tool if any issues are found.<br>
But the folliwing additional actions are available:<br>

- **Create a new issue** - create a new issue with detailed report about the issue.
- **Reject image** - automatically reject the image if working in the Labeling Queue.

![Application Settings](https://github.com/user-attachments/assets/20c20b9c-1460-4a64-8c42-03eaa029a9a5)

# Available checks
The application has a set of predefined checks that can be enabled or disabled. The following checks are available:<br>

- **No objects found on the image** - the test will fail if no objects are found on the image.
- **Not all of the classes in the Project Meta a present on the image** - the test will fail if not all of the classes in the Project Meta are present on the image.
- **Area of the label differs from the average area of labels of the same class** - the test will fail if the area of the label differs from the average area of labels of the same class by more than the specified threshold. If this test is enabled, it's possible to specify the threshold.
- **Number of objects of the same class on the image differs from the average number of objects of the same class** - the test will fail if the number of objects of the same class on the image differs from the average number of objects of the same class by more than the specified threshold. If this test is enabled, it's possible to specify the threshold.s

![Available checks](https://github.com/user-attachments/assets/822835d8-2650-434a-8d94-0da7fe9b9e3e)

# How To Run
**Step 1:** Run the appliaction from the `Ecosystem` page.<br>

![Run in Ecosystem](https://github.com/user-attachments/assets/1ad6d7fe-fcd2-4fdc-b45c-fc0d6bd870d7)

**Step 2:** Open the Image Labeling Tool.<br>
**Step 3:** Open the `Apps` tab and find `Real-time Labeling Quality Check` app.<br>

![Run in Labeling Tool](https://github.com/user-attachments/assets/6ca1cd7d-c2e5-4d6b-bc16-99d345786a1e)

**Step 4:** Click on `Open` button.<br>
**Step 5 (optional):** Configure the application: choose the needed checks and actions.<br>

Now you can start labeling images. The application will run in the background and check the labels in real-time. If any issues are found, the application will notify you about them by notification in the Labeling Tool and process other actions depending on the settings.

# Using the results
Depending on the selected action, the application will show a notification in the Labeling Tool, create a new issue with detailed report or automatically reject the image if working in the Labeling Queue.

## Interactive notifications
The basic way to notify the user about the failed test is to show a notification in the Labeling Tool. Here are some examples of how the notification looks like:

![Errors in the Labeling Tool](https://github.com/user-attachments/assets/2434571b-15c9-4483-8c14-091cd1b49c14)

### Working with issues
If the "Create a new issue" action is selected, the application will create issues and add reports to them. There are two common types of checks: image related and figure (label) related. The first type is for the cases where is no exact label, which failed the test (for example if there are no objects on the image). The second type is for the cases where the exact label failed the test (for example if the area of the label differs from the average area of labels of the same class). And they will be handled differently.

#### Image related checks
If there's no specific label that failed the test, the issue will be created with the report which looks like this:

![Image related issue](https://github.com/user-attachments/assets/a8398abf-1a75-4c3e-a6f2-070b2aa3bad1)

As you can see it contains some metadata about the image and the failed test, and also a link to the image.

#### Label related checks
If there's a specific label that failed the test, the issue will be created with the report which looks like this:

![Label related issue](https://github.com/user-attachments/assets/342c0340-7585-47a9-9c56-f3ac132b81fd)

In this case you'll find the visualization of the label before (on the moment of the test) and after the correction, and also some metadata about the label and the failed test. It should be more convenient to understand what's wrong with the label and how to fix it.

### Rejecting images
If the "Reject image" action is selected and the app is launched inside of the Labeling Queue, the image will be automatically rejected if the test fails. It's a very convenient way to filter out the images that don't meet the requirements and instantly return them back to the queue for correction.