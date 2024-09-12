<div align="center" markdown>
<img src="https://github.com/user-attachments/assets/1f2782b2-7eda-43fa-8368-af794f0782ee"/>  

# Intellisense

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#Avaiable actions">Avaiable actions</a> •
  <a href="#Available checks">Available checks</a> •
  <a href="#How-To-Run">How To Run</a> •
  <a href="#Using the results">Using the results</a>
</p>

[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervise.ly/apps/supervisely-ecosystem/intellisense)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/intellisense)
[![views](https://app.supervise.ly/img/badges/views/supervisely-ecosystem/intellisense.png)](https://supervise.ly)
[![runs](https://app.supervise.ly/img/badges/runs/supervisely-ecosystem/intellisense.png)](https://supervise.ly)

</div>

# Overview
This application is designed to be an assistant for data labeling. It helps to find incorrect labels by predefined rules and highlight them in different ways. For example: show simple notification in the Labeling Tool, create a new issue with detailed report or even automatically reject the image if working in the [Labeling Queue](https://supervisely.com/blog/labeling-queues/).<br>

# Avaiable actions
By default the application will show a notification in the Labeling Tool if any issues are found.<br>
But the folliwing additional actions are available:<br>

- **Create a new issue** - create a new issue with detailed report about the issue.
- **Reject image** - automatically reject the image if working in the Labeling Queue.

![Application Settings](URL_HERE)

# Available checks
The application has a set of predefined checks that can be enabled or disabled. The following checks are available:<br>

- **No objects found on the image** - the test will fail if no objects are found on the image.
- **Not all of the classes in the Project Meta a present on the image** - the test will fail if not all of the classes in the Project Meta are present on the image.
- **Area of the label differs from the average area of labels of the same class** - the test will fail if the area of the label differs from the average area of labels of the same class by more than the specified threshold. If this test is enabled, it's possible to specify the threshold.
- **Number of objects of the same class on the image differs from the average number of objects of the same class** - the test will fail if the number of objects of the same class on the image differs from the average number of objects of the same class by more than the specified threshold. If this test is enabled, it's possible to specify the threshold.s

![Available checks](URL_HERE)

# How To Run
**Step 1:** PASS.

# Using the results
Depending on the selected action, the application will show a notification in the Labeling Tool, create a new issue with detailed report or automatically reject the image if working in the Labeling Queue.

## Interactive notifications
The basic way to notify the user about the failed test is to show a notification in the Labeling Tool. Here are some examples of how the notification looks like:

![No objects on the image notification](URL_HERE)
![Not all classes on the image notification](URL_HERE)

### Working with issues
If the "Create a new issue" action is selected, the application will create issues and add reports to them. There are two common types of checks: image related and figure (label) related. The first type is for the cases where is no exact label, which failed the test (for example if there are no objects on the image). The second type is for the cases where the exact label failed the test (for example if the area of the label differs from the average area of labels of the same class). And they will be handled differently.

#### Image related checks
If there's no specific label that failed the test, the issue will be created with the report which looks like this:

![No objects on the image issue](URL_HERE)

As you can see it contains some metadata about the image and the failed test, and also a link to the image.

#### Label related checks
If there's a specific label that failed the test, the issue will be created with the report which looks like this:

![Area of the label differs from the average area](URL_HERE)

In this case you'll find the visualization of the label before (on the moment of the test) and after the correction, and also some metadata about the label and the failed test. It should be more convenient to understand what's wrong with the label and how to fix it.

### Rejecting images
If the "Reject image" action is selected and the app is launched inside of the Labeling Queue, the image will be automatically rejected if the test fails. It's a very convenient way to filter out the images that don't meet the requirements and instantly return them back to the queue for correction.