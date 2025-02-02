# Comprehensive Report for Event Management Project

## Introduction
This project is a web application developed in Flask, designed for managing events and participants. The application allows the creation of events, the addition of participants, the modification of participant statuses, and the sending of certificates via email. The system is designed to be intuitive and easy to use, providing a user-friendly interface for users.

## Project Objectives
- **Manage Events**: Allow the creation, viewing, and editing of events.
- **Manage Participants**: Facilitate the addition, editing, and removal of participants in events.
- **Send Certificates**: Generate and send participation certificates via email to participants who attended the event.
- **User-Friendly Interface**: Provide a smooth and intuitive user experience.

## Project Structure
The project structure is organized into directories and files that facilitate maintenance and scalability. The main components include:
- **app.py**: The main file that initializes the Flask application and configures routes and environment variables.
- **routes.py**: Contains the route definitions for the application, including the logic for managing events and participants.
- **templates/**: Directory that stores the HTML templates used to render the application's pages.
- **uploads/**: Directory where the generated certificates are stored.
- **.env**: File that contains environment variables, such as email credentials, which should not be exposed in the code.

## Main Functionalities

### 1. Event Management
The application allows users to create events, defining details such as name, date, duration, and trainer. Events can be viewed in a list, and users can access specific details of each event.

### 2. Participant Management
Users can add participants to an event, assigning each one a status that can be changed as needed. Statuses include "pending," "confirmed," "present," and "canceled." The application also allows the viewing of all participants associated with an event.

### 3. Sending Certificates
One of the most important functionalities of the application is the ability to generate PDF certificates for participants who attended the event. After generation, the certificates are sent via email to the participants, ensuring they receive confirmation of their attendance.

## Technologies Used
- **Flask**: Web framework used to develop the application.
- **SQLAlchemy**: Library for interacting with the database.
- **Jinja2**: Template engine used to render HTML pages.
- **SMTP**: Protocol used to send emails.
- **Python-dotenv**: Library for loading environment variables from a .env file.

## Conclusion
The project is a well-structured Flask application that allows the management of events and participants, as well as the sending of certificates via email. The main functionalities include event creation, participant management, and certificate sending, all with a user-friendly interface.

If you need more details or help with any specific part of the code, feel free to ask!
